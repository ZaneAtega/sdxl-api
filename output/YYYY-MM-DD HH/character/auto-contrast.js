#target photoshop

var PRIORITIZE_SAVE_SPEED = false; // OPTIMIZE_FILE_SIZE = true;
var contents = new Folder(new File($.fileName).parent).getFiles();
var files = [];

for (var i = 0; i < contents.length; i++) {
    var f = contents[i];

    if (f instanceof Folder) {
        files = files.concat(f.getFiles(function (f) {
            return f instanceof File && /\.png$/i.test(f.name);
        }));
    } else if (/\.png$/i.test(f.name)) {
        files.push(f); 
    }
}

for (var i = 0; i < files.length; i++) {
    var doc = open(files[i]);

    var desc = new ActionDescriptor();
    desc.putBoolean(charIDToTypeID("AuCo"), true);
    executeAction(charIDToTypeID("Lvls"), desc, DialogModes.NO);

    var output = new File(files[i].parent + "/" + files[i].name.replace(/\.png$/i, "_auto_contrast.png"));

    var orig = new Folder(files[i].parent + "/orig");
    if (!orig.exists) orig.create();
    files[i].copy(new File(orig + "/" + files[i].name));
    files[i].remove();

    if (PRIORITIZE_SAVE_SPEED) {
        doc.saveAs(output, new PNGSaveOptions(), true, Extension.LOWERCASE);
        doc.close(SaveOptions.DONOTSAVECHANGES);
        continue;
    }

    var options = new ExportOptionsSaveForWeb();
    options.format = SaveDocumentType.PNG;
    options.PNG8 = false;
    options.transparency = true;
    options.interlaced = false;
    options.quality = 100;
    doc.exportDocument(output, ExportType.SAVEFORWEB, options);

    doc.close(SaveOptions.DONOTSAVECHANGES);
}