/* columns.js - split lists with class columns2/columns3/columns4
 * to equal length columns.
 *
 * Copyright 2014 Christophe Siraut - Licensed under GNU Public License 2.1 or later
 * @source: http://git.domainepublic.net/?p=columnsjs.git
 */

function columns(src, nb) {
  var origList = src;
  var cols = new Array();
  var items = origList.getElementsByTagName('li');
  var container = document.createElement('div');
  var itemsLength;
  var n = nb;
  for (i=1; i <= nb; i++) {
      cols[i] = document.createElement('ul');
      itemsLength = items.length/n;
      for (j = 0; j < itemsLength; j++) {
          cols[i].appendChild(items[0]);}
      cols[i].setAttribute('style', 'float:left; margin:0 32px 0 0; padding:0px; list-style: none;');
      container.appendChild(cols[i]);
      n--;
      console.log(items.length);
  }
  container.style.overflow = "hidden";
  origList.parentNode.replaceChild(container, origList);
}

function onload() {
  var uls = document.getElementsByTagName('ul');
  for (var i=0; i< uls.length; i++) {
    if (uls[i].getAttribute('class') == 'columns2')
      columns(uls[i], 2);
    if (uls[i].getAttribute('class') == 'columns3')
      columns(uls[i], 3);
    if (uls[i].getAttribute('class') == 'columns4')
      columns(uls[i], 4);
  }
}

window.addEventListener('load', onload, false);
