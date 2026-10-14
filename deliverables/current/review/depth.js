const img=document.querySelector('#depth-image'),link=document.querySelector('#depth-image-link');
const depthCases=JSON.parse(document.querySelector('#review-data').textContent).depth_cases;
document.querySelectorAll('[data-depth-case]').forEach(button=>button.addEventListener('click',()=>{
  const value=button.dataset.depthCase;
  img.src=`views/depth_${value}.svg`;link.href=img.src;
  const body=document.querySelector('#depth-values tbody');body.replaceChildren();
  for(const stud of depthCases[value].studs){const row=document.createElement('tr');for(const value of [stud.id,stud.tip_z_mm.toFixed(1),stud.cover_rear_z_mm.toFixed(1),stud.tip_to_cover_rear_clearance_mm.toFixed(1)]){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}body.append(row);}
  document.querySelectorAll('[data-depth-case]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
}));
document.querySelector('#show-depth-3d').addEventListener('click',()=>{
  document.querySelector('[data-state="proposed"]').click();
  document.querySelector('[data-view="studs"]').click();
});
