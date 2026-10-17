'use strict';
const rows = document.querySelector('#file-rows');
const search = document.querySelector('#search');
const category = document.querySelector('#category');
let catalog = [];
function renderLibrary() {
  const query = search.value.trim().toLocaleLowerCase();
  const found = catalog.filter(item => (category.value === 'all' || item.category === category.value) && `${item.title} ${item.description} ${item.path}`.toLocaleLowerCase().includes(query));
  rows.replaceChildren();
  for (const item of found) {
    const tr = document.createElement('tr');
    const name = document.createElement('td');
    const link = document.createElement('a');
    link.href = item.url; link.textContent = item.title;
    if (!item.url.endsWith('.html')) link.download = '';
    name.append(link);
    const source = document.createElement('small'); source.textContent = item.storage === 'Site' ? 'HOSTED HERE' : 'LARGE ORIGINAL · GITHUB'; name.append(source);
    const purpose = document.createElement('td'); purpose.textContent = item.description;
    const type = document.createElement('td'); type.textContent = item.path.split('.').pop().toUpperCase();
    const size = document.createElement('small'); size.textContent = `${item.size_mb.toFixed(2)} MB`; type.append(size);
    tr.append(name, purpose, type); rows.append(tr);
  }
  document.querySelector('#result-count').textContent = `${found.length} of ${catalog.length} handoff files`;
  document.querySelector('#empty').hidden = found.length !== 0;
}
search.addEventListener('input', renderLibrary);
category.addEventListener('change', renderLibrary);
fetch('/catalog.json').then(response => { if (!response.ok) throw new Error(response.status); return response.json(); }).then(data => { catalog = data; renderLibrary(); }).catch(() => { document.querySelector('#result-count').textContent = 'The file library could not load. Use the direct downloads above or the complete inventory.'; });
