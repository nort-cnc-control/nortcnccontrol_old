require([
    "dojo", // body
    "dojo/dom", // byId
    "app/Desktop", // Desktop
    "dojo/domReady!"
], function(dojo, dom, Desktop){
    var desktop = new Desktop({});

    dom.byId("loadingIndicator").remove(); //Удаляем индикатор загрузки, он больше не нужен
    desktop.placeAt(dojo.body());
    desktop.startup();
});