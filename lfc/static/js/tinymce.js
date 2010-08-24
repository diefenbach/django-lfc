// function CustomFileBrowser(field_name, url, type, win) {
// 
//     url = "/manage/filebrowser?obj_id=" + $("#obj-id").attr("data"),
//     url = url + "&type=" + type;
// 
//     tinyMCE.activeEditor.windowManager.open({
//         file: url,
//         width: 820,  // Your dimensions may differ - toy around with them!
//         height: 500,
//         resizable: "yes",
//         scrollbars: "yes",
//         inline: "no",
//         close_previous: "no"
//     }, {
//         window: win,
//         input: field_name,
//         editor_id: tinyMCE.selectedInstance.editorId
//     });
//     return false;
// }
// 
// tinyMCE.init({
//     mode: "none",
//     theme : "advanced",
//     height : "400",
//     tab_focus : ":prev,:next",
//     button_tile_map : true,
//     plugins : "advimage, safari, fullscreen",
//     convert_urls : false,
//     theme_advanced_buttons1 : "bold, italic, underline, |, justifyleft," +
//                               "justifycenter, justifyright, justifyfull, |," +
//                               "bullist,numlist, |, outdent, indent, |, image, |, undo," +
//                               "redo, |, code, link, unlink, styleselect, formatselect, |," +
//                               "removeformat, fullscreen",
//     theme_advanced_buttons2: "",
//     theme_advanced_buttons3: "",
//     theme_advanced_buttons4: "",
//     theme_advanced_toolbar_location : "top",
//     theme_advanced_toolbar_align : "left",
//     content_css : "/media/tiny.css",
//     file_browser_callback: "CustomFileBrowser"
// })