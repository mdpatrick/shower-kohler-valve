"""Read current FT01 design evidence without relabeling historical geometry.

No imports of builders, no mutations, and no physical approval inferred from an
exact solid or a positive projected margin. Historical queries stay explicit.
"""
from pathlib import Path
import hashlib
import json
import math


class QueryError(ValueError):
    pass


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def nested(value,path):
    try:
        for key in path.split('.'):
            value=value[int(key)] if isinstance(value,list) else value[key]
        return value
    except (KeyError,ValueError,TypeError,IndexError):
        raise QueryError(f'Unknown current design path: {path}. Use main.*, diverter.*, stocks.0.*, or an exact measurement ID; historical resolved paths require query historical dimension.') from None


class CurrentQuery:
    def __init__(self,root):
        self.root=Path(root)
        self.folder=Path('deliverables/current/fabrication/fit-trial')
        self.design=self.read('canon/fit_trial_design.json')
        self.state=self.read('canon/project_state.json')
        self.measurements=self.read('canon/measurements.json')

    def read(self,path):
        return json.loads((self.root/path).read_text())

    def source(self,path):
        return {'path':str(path),'sha256':digest(self.root/path)}

    def response(self,result,method,state='current_quote_and_dry_fit_design',sources=()):
        return dict(units='mm unless a field explicitly states otherwise',
                    design_revision=self.design['revision'],evidence_revision=self.measurements['revision'],
                    state=state,design_status=self.design['status'],method=method,
                    sources=[self.source(p) for p in sources],result=result,
                    physical_fit=self.state['readiness']['physical_fit'],permanent_installation_release=False)

    def report(self):
        path=self.folder/'design_report.json';report=self.read(path)
        if report['design']!=self.design or report['revision']!=self.design['revision']:
            raise QueryError('Stale fit-trial report: rebuild with ./project prepare-fit-trial --stage analysis before querying derived results.')
        for rel,expected in report['sources_sha256'].items():
            if not (self.root/rel).is_file() or digest(self.root/rel)!=expected:
                raise QueryError(f'Stale fit-trial source: {rel}. Rebuild the dependent analysis before using these results.')
        return report

    def dimension(self,key):
        matches=[m for m in self.measurements['measurements'] if m['id']==key]
        if matches:
            return self.response(matches,'Read recorded measurement with its original status and provenance',
                                 state='measurement_record',sources=['canon/measurements.json'])
        aliases={'candidate.diameter_mm':'main.outer_diameter_mm',
                 'candidate.thickness_mm':'stocks.0.thickness_mm',
                 'candidate.aperture_width_mm':'main.aperture_width_mm',
                 'candidate.aperture_height_mm':'main.aperture_height_mm',
                 'candidate.aperture_radius_mm':'main.aperture_radius_mm',
                 'candidate.aperture_center_mm':'main.aperture_center_mm'}
        canonical=aliases.get(key,key)
        result={'path':canonical,'value':nested(self.design,canonical),
                'provenance':'Current dimensional design input; not a physical measurement'}
        if key!=canonical:result['compatibility_alias']=key
        return self.response(result,'Read current design input',sources=['canon/fit_trial_design.json'])

    def coverage(self,feature_id=None):
        report=self.report()
        resolved=self.read('data/derived/resolved.json')
        placements=self.read('deliverables/current/fabrication/control-registration/registration_trial.json')
        features=[f for f in resolved['features'] if f.get('include_in_coverage')]
        if feature_id and feature_id not in [f['id'] for f in features]:
            raise QueryError(f'{feature_id} has no current per-feature main-plate trace calculation. Use coverage without an ID for the documented main traces and limited diverter summary.')
        radius=self.design['main']['outer_diameter_mm']/2
        cases=[]
        for pose in placements['cases']:
            center=pose['main_center_installed_mm'];scale=pose['scan_scale_trial']
            margins=[]
            for f in features:
                points=[(x*scale,y*scale) for x,y in f['contour_mm']]
                point=max(points,key=lambda p:math.dist(p,center))
                raw=radius-math.dist(point,center)
                allowance=scale*f.get('trace_allowance_mm_at_R001',0)
                margins.append(dict(feature_id=f['id'],feature_status=f['status'],
                    limit_point_installed_mm=point,outer_margin_before_trace_mm=raw,
                    trace_allowance_mm=allowance,outer_margin_after_trace_mm=raw-allowance,
                    computed_outline_coverage='POSITIVE_PROJECTED_MARGIN' if raw>=allowance else 'FAIL_OUTLINE_COVERAGE',
                    criterion='Outer-circle margin after the trace allowance is nonnegative; this is not the required sound-support/seal allowance.',
                    result_status='UNRESOLVED_FIELD_FIT',
                    source=f['source'],unknowns=['absolute scan/feature error','actual pose','unseen damage','sound support/seal land']))
            worst=min(margins,key=lambda m:m['outer_margin_after_trace_mm'])
            saved=next(c for c in report['placement_scenarios'] if c['state']==pose['id'])
            if not math.isclose(worst['outer_margin_after_trace_mm'],saved['main_margin_after_trace_mm'],abs_tol=1e-8):
                raise QueryError('Current per-feature calculation disagrees with the saved minimum; inspect the analysis before use.')
            cases.append(dict(state=pose['id'],scan_scale_trial=scale,main_center_mm=center,
                main_diameter_mm=radius*2,limiting_feature=worst['feature_id'],
                minimum_margin_after_trace_mm=worst['outer_margin_after_trace_mm'],
                features=[m for m in margins if not feature_id or m['feature_id']==feature_id],
                gap_main_diverter_mm=saved['gap_main_diverter_mm'],gap_main_fallback_mm=saved['gap_main_fallback_mm']))
        return self.response({'scenarios':cases,
            'diverter_summary':{'method':'Read saved circle/trace estimate in original pose only; no per-feature diverter certification',
                'margin_original_pose_mm':report['diverter_damage_margin_original_pose_mm'],
                'outside_diameter_mm':self.design['diverter']['outer_diameter_mm']},
            'scope':'Recomputed outer-circle margin to documented projected MAIN traces, with their trace allowance. Does not test whether the aperture exposes damage, oblique visibility, sound support or water sealing. Three pose hypotheses are not error bounds.'},
            'Recomputed analytic distance from current circle to stored projected trace vertices',
            state='unselected_placement_scenarios',
            sources=['canon/fit_trial_design.json','data/derived/resolved.json',self.folder/'design_report.json',
                     'deliverables/current/fabrication/control-registration/registration_trial.json'])

    def solid(self,identifier,stock=None):
        report=self.report()
        aliases={'CUSTOM-01':'MAIN','DIVERTER':'DIV','FALLBACK':'DIV-FALLBACK'}
        kind=aliases.get(identifier,identifier)
        selected=stock or self.design['stocks'][0]['id']
        parts=[p for p in report['parts'] if p['id']==identifier or (p['kind']==kind and p['stock']==selected)]
        if len(parts)!=1:
            raise QueryError('Specify solid MAIN|DIV|DIV-FALLBACK [stock ID], or an exact current part ID. Factory reference solids require query historical solid PLATE-INNER|TRIM-OUTER.')
        part=parts[0]
        if stock and part['stock']!=stock:raise QueryError('Part ID and requested stock disagree.')
        path=self.folder/part['files']['step']
        if digest(self.root/path)!=part['sha256']['step']:
            raise QueryError('STEP bytes differ from the current design report; rebuild/audit before querying.')
        import cadquery as cq
        solid=cq.importers.importStep(str(self.root/path)).val();b=solid.BoundingBox()
        result={'id':part['id'],'stock':part['stock'],'bounds_local_mm':[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]],
                'volume_mm3':solid.Volume(),'is_valid':solid.isValid(),'solid_count':len(solid.Solids()),
                'frame':'Part-local X/Y center at circle center; rear Z=0, front Z=thickness. No installed pose inferred.'}
        if identifier in aliases:result['compatibility_alias']=identifier
        return self.response(result,'Reimported and queried exact OCCT STEP solid of the current custom part',sources=[path,self.folder/'design_report.json'])

    def clearance(self):
        r=self.report()
        return self.response({k:r[k] for k in ['placement_scenarios','geometric_check_scope','inner_opening_envelopes',
                     'nominal_foam_extra_land_mm','foam_corner_sensitivity','tolerance_budget','physical_checks']},
                     'Read saved, source-hash-checked projected hardware and nominal foam checks; no new intersection computation',
                     state='unselected_placement_scenarios',sources=[self.folder/'design_report.json'])

    def depth(self):
        d=self.design
        return self.response(dict(added_height=d['depth'],stocks=d['stocks'],
             effective_bedding_height_mm=None,actual_compressed_foam_height_mm=None,
             installed_rod_projection_mm=None,actual_adapter_engagement_mm=None,
             current_full_stack_fit='UNRESOLVED: no measured complete FT01 assembly',
             actual_fit_record=str(self.folder/'expert_visit_record_FT01.pdf'),
             historical_diagnostic='query historical depth shows older assumed solids and rough-in comparisons, not the current FT01 installed assembly'),
             'Read current depth inputs and explicitly unknown field values',sources=['canon/fit_trial_design.json'])

    def compare_states(self):
        r=self.report()
        return self.response(dict(physical_selected_arrangement=self.state['states']['selected_arrangement'],
             proposed_design=r['design'],placement_scenarios=r['placement_scenarios'],
             source_capture_state=self.state['states']['current_exposed_installation'],
             attached_scan='Separate supplemental capture; not globally registered to primary scan',
             observed_geometry_changed=False,changes='Current custom parts use FT01 dimensions. Prior placement hypotheses remain separate and unselected. No physical valve/stud adjustment is inferred.'),
             'Read current design and preserved scenario records',state='observed_and_proposed_distinguished',
             sources=['canon/project_state.json',self.folder/'design_report.json'])

    def help(self):
        return self.response({'operations':['dimension main.outer_diameter_mm','dimension stocks.0.thickness_mm',
             'dimension <measurement-ID>','coverage [CUT-03]','clearance','depth',
             'solid MAIN|DIV|DIV-FALLBACK [T1524|T3000]','solid <exact current part-ID>',
             'compare-states','features [ID]','measure <landmark-ID> <landmark-ID>',
             'historical dimension candidate.diameter_mm','historical solid PLATE-INNER|TRIM-OUTER',
             'historical section controls|studs','historical depth','validate'],
             'default':'Current fit-trial design; source measurements remain their own evidence revision.',
             'historical':'Explicit access to older R005 reconstruction and its rejected trial assembly. Never a current FT01 fit check.',
             'scope':'features/measure inspect the preserved evidence registry. section/reconcile-centers retain historical diagnostic scope, explicitly labeled.'},
             'Query command reference',sources=['canon/fit_trial_design.json'])

    def run(self,args):
        op=args[0] if args else 'help';params=args[1:]
        arity={'help':(0,0),'dimension':(1,1),'coverage':(0,1),'solid':(1,2),
               'clearance':(0,0),'depth':(0,0),'compare-states':(0,0)}
        if op not in arity:raise QueryError(f'Unknown current operation {op}; run ./project query for help.')
        lo,hi=arity[op]
        if not lo<=len(params)<=hi:raise QueryError(f'{op} expects {lo}'+(f'-{hi}' if lo!=hi else '')+' argument(s); run ./project query for help.')
        return getattr(self,op.replace('-','_'))(*params)
