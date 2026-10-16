#target photoshop

var prioritizeSaveSpeed = false; // optimizeFileSize = true;

var folder = new Folder(new File($.fileName).parent);

var files = folder.getFiles(function (f) {
    return f instanceof File && /\.png$/i.test(f.name);
});

for (var i = 0; i < files.length; i++) {
    var doc = open(files[i]);
    var output = new File(folder.fsName + "/" + files[i].name.replace(/\.png$/i, "_auto_contrast.png"));

    var desc = new ActionDescriptor();
    desc.putBoolean(charIDToTypeID("AuCo"), true);
    executeAction(charIDToTypeID("Lvls"), desc, DialogModes.NO);

    if (prioritizeSaveSpeed) {
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