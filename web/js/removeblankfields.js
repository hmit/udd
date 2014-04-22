function removeBlankFields(form) {
    var inputs = form.getElementsByTagName("input");
    var removeList = new Array();
    for (var i=0; i<inputs.length; i++) {
        if (inputs[i].value == "") {
            removeList.push(inputs[i]);
        }
    }
    for (x in removeList) {
        removeList[x].parentNode.removeChild(removeList[x]);
    }
}
