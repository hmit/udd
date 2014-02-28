function twoCols(src) {
  var origList = src;

  var leftList = document.createElement('ul');
  var rightList = document.createElement('ul');
  var container = document.createElement('div');

  var items = origList.getElementsByTagName('LI');

  var itemsLength = items.length/2;
  for (i = 0; i < itemsLength; i++) {
    leftList.appendChild(items[0]);
    }

  itemsLength = items.length;
  for (i = 0; i < itemsLength; i++) {
    rightList.appendChild(items[0]);
    }
  container.appendChild(leftList);
  container.appendChild(rightList);

  leftList.setAttribute('class', 'left');
  rightList.setAttribute('class', 'right');
  container.setAttribute('class','twocol');
  origList.parentNode.replaceChild(container, origList);
}

function allTwoCols (whichclass) {
  var uls = document.getElementsByTagName('ul');
  for (var i=0; i< uls.length; i++) {
    if (uls[i].getAttribute('class') == whichclass || 
        uls[i].getAttribute('className') == whichclass)
      { twoCols(uls[i]); }
    }
}


function threeCols(src) {
  var origList = src;

  var leftList = document.createElement('ul');
  var centerList = document.createElement('ul');
  var rightList = document.createElement('ul');
  var container = document.createElement('div');

  var items = origList.getElementsByTagName('LI');

  var itemsLength = items.length/3;
  for (i = 0; i < itemsLength; i++) {
    leftList.appendChild(items[0]);
    }

  itemsLength = items.length/2;
  for (i = 0; i < itemsLength; i++) {
    centerList.appendChild(items[0]);
    }
  itemsLength = items.length;
  for (i = 0; i < itemsLength; i++) {
    rightList.appendChild(items[0]);
    }
  container.appendChild(leftList);
  container.appendChild(centerList);
  container.appendChild(rightList);

  leftList.setAttribute('class', 'left');
  centerList.setAttribute('class', 'left');
  rightList.setAttribute('class', 'right');
  container.setAttribute('class','threecol');
  origList.parentNode.replaceChild(container, origList);
}

function allThreeCols (whichclass) {
  var uls = document.getElementsByTagName('ul');
  for (var i=0; i< uls.length; i++) {
    if (uls[i].getAttribute('class') == whichclass || 
        uls[i].getAttribute('className') == whichclass)
      { threeCols(uls[i]); }
    }
}
