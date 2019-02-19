define([
    "dojo/_base/declare",
    "dojo/_base/lang",
    "dijit/layout/LayoutContainer",
    "dijit/layout/BorderContainer",
    "dijit/layout/ContentPane",
    "dijit/Toolbar",
    "dijit/ToolbarSeparator",
    "dijit/form/Button",
    "dijit/form/SimpleTextarea",
    "dijit/form/TextBox"
], function(
    declare,
    lang,
    LayoutContainer,
    BorderContainer,
    ContentPane,
    Toolbar,
    ToolbarSeparator,
    Button,
    SimpleTextarea,
    TextBox,
) {
	return declare("app.Desktop", [LayoutContainer],
		{
			class: "desktop", // CSS-class for desktop
			buildRendering: function() {
				this.inherited(arguments);

				this.toolbar = new Toolbar({region: "top"});

				this.addChild(this.toolbar);

				this.loadButton = new Button({
					label: "Загрузка",
					"class": "alt-primary"
				});
				this.startButton = new Button({
					label: "Старт",
					"class": "alt-success"
				});
				this.continueButton = new Button({
					label: "Продолжить",
					"class": "alt-success"
				});
				this.stopButton = new Button({
					label: "Стоп",
					"class": "alt-danger"
				});
				this.homeXYZButton = new Button({
					label: "Home XYZ"
				});
				this.probeZButton = new Button({
					label: "Probe Z"
				});

				this.toolbar.addChild(this.loadButton);
				this.toolbar.addChild(new ToolbarSeparator({}));
				this.toolbar.addChild(this.startButton);
				this.toolbar.addChild(this.continueButton);
				this.toolbar.addChild(this.stopButton);
				this.toolbar.addChild(new ToolbarSeparator({}));
				this.toolbar.addChild(this.homeXYZButton);
				this.toolbar.addChild(this.probeZButton);


				this.gcode = new SimpleTextarea(
					{
						name: "gcode-editor",
						region:"main",
						rows: "40",
						cols: "120"
					})
				this.addChild(this.gcode);

				this.command = new TextBox({name: "command", region:"bottom"})
				this.addChild(this.command)
			}
		});
});

