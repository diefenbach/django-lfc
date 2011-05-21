var editor;

function insertHTML(html) {
    editor.focus();
    editor.execCommand("inserthtml", html, null, null);    
}

function getSelectedText() {
    return editor.selectedText()
}

function addEditor(selector) {
    $(selector).cleditor();
}

// Display image browser
function imagebrowser(e, data) {
    editor = data.editor;
    editor.focus();
    var id = $("#obj-id").attr("data");
    $.get("/manage/imagebrowser?obj_id=" + id, function(data) {
        $("#overlay-2 .content").html(data);
    });
    overlay_2.load();
    $("#overlay-2").css("left", ($(document).width() - 1000) / 2);
}

// Display File browser
function filebrowser(e, data) {
    editor = data.editor;
    editor.focus();
    var id = $("#obj-id").attr("data");
    $.get("/manage/filebrowser?obj_id=" + id, function(data) {
        $("#overlay-2 .content").html(data);
    });
    overlay_2.load();
    $("#overlay-2").css("left", ($(document).width() - 1000) / 2);
}

$(function() {

    $.cleditor.defaultOptions.width = 670;
    $.cleditor.defaultOptions.height = 400;
    $.cleditor.defaultOptions.controls = "bold italic underline strikethrough subscript superscript " +
                                         "style | color highlight removeformat | bullets numbering | outdent " +
                                         "indent | alignleft center alignright justify | undo redo | " +
                                         "myimage myfile unlink | html"

    $.cleditor.defaultOptions.docCSSFile = "/media/tiny.css";
    $.cleditor.defaultOptions.styles = [["Paragraph", "<p>"], ["Header 1", "<h1>"], ["Header 2", "<h2>"], ["Header 3", "<h3>"], ["Quote", "<blockquote>"]]

    // Image plugin
    $.cleditor.buttons.myimage = {
        name: "myimage",
        image: "image.gif",
        title: "Insert Image",
        useCSS: true,
        buttonClick: imagebrowser,
    };

    // File plugin
    $.cleditor.buttons.myfile = {
        name: "myfile",
        image: "link.gif",
        title: "Insert File",
        useCSS: true,
        buttonClick: filebrowser,
    };
});