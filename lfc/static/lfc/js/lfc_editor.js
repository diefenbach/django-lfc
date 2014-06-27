var current_view;

function display_mail() {
    $(".content-form").hide();
    $(".extern-form").hide();
    $(".email-form").show();
    current_view = "mail";
}

function display_content() {
    $(".content-form").show();
    $(".extern-form").hide();
    $(".email-form").hide();
    current_view = "content";
}

function display_extern() {
    $(".content-form").hide();
    $(".extern-form").show();
    $(".email-form").hide();
    current_view = "extern";
}

$(function() {
    $(document).on("click", "a.content-form-link", function() {
        display_content();
        return false;
    });

    $(document).on("click", "a.email-form-link", function() {
        display_mail();
        return false;
    });

    $(document).on("click", "a.extern-form-link", function() {
        display_extern();
        return false;
    });

    $(document).on("click", "input.image", function() {
        var html = "<img src='" + $(this).attr("value") + "' />"
        $("#image-preview").html(html)
    })

    $(document).on("click", "#insert-file", function() {
        var html;
        var title = $("#fb-title").val();
        var target = $("#fb-target").val();

        // This is just the selected content of the link
        var text = getSelectedText();

        if (current_view == "content") {
            var url = $("input.child:checked").attr("value");
            if (url)
                html = "<a href='" + url + "' title='" + title + "' target='" + target + "'>" + text + "</a>"
        }

        if (current_view == "extern") {
            var url = $("input.fb-extern").val();
            if (url) {
                var protocol = $(".fb-extern-protocol").val();
                html = "<a href='" + protocol + url + "' title='" + title + "' target='" + target + "'>" + text + "</a>"
            }
        }

        if (current_view == "mail") {
            var email = $("input.fb-email").val();
            if (email != "")
                html = "<a href='mailto:" + email + "' title='" + title + "' target='" + target + "'>" + text + "</a>"
        }

        if (html) {
            var node = getSelectedNode();
            if (node.nodeName == "A")
                $(node).replaceWith(html);
            else
                insertHTML(html);
        }

        $("#overlay").dialog("close");
        return false;
    });

    $(document).on("click", "#insert-image", function() {
        var url = $("input.image:checked").attr("value");
        var size = $("#image-size").val();
        var klass = $("#image-class").val();

        if (size)
            url = url.replace("200x200", size);
        else
            url = url.replace(".200x200", "");

        if (klass)
            html = "<img class='" + klass + "' src='" + url + "' />"
        else
            html = "<img src='" + url + "' />"

        insertHTML(html);
        $("#overlay").dialog("close");
        return false;
    })

    $(document).on("click", "a.fb-obj", function() {
        var title = $("#fb-title").val();
        var target = $("#fb-target").val();
        var url = $(this).attr("href");
        var id = $("#obj-id").attr("data");
        $.get(url + "&current_id=" + id + "&title=" + title + "&target=" + target, function(data) {
            data = $.parseJSON(data);
            $("#overlay .content").html(data["html"]);
            display_content();
        });
        return false;
    });
});
