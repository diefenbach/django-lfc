$(function() {
    $("a.content-form-link").live("click", function() {
        $(".content-form").show();
        $(".extern-form").hide();
        $(".email-form").hide();
        return false;
    });

    $("a.email-form-link").live("click", function() {
        $(".content-form").hide();
        $(".extern-form").hide();
        $(".email-form").show();
        return false;
    });

    $("a.extern-form-link").live("click", function() {
        $(".content-form").hide();
        $(".extern-form").show();
        $(".email-form").hide();
        return false;
    });

    $("input.image").live("click", function(e) {
        var html = "<img src='" + $(this).attr("value") + "' />"
        $("#image-preview").html(html)
    })

    $("#insert-file").live("click", function(e) {
        var html;

        if (!html) {
            var url = $("input.child:checked").attr("value");
            if (url)
                html = "<a href='" + url + "'>" + getSelectedText() + "</a>"
        }

        if (!html) {
            var url = $("input.fb-extern").val();
            if (url) {
                var protocol = $(".fb-extern-protocol").val();
                html = "<a href='" + protocol + url + "'>" + getSelectedText() + "</a>"
            }
        }

        if (!html) {
            var email = $("input.fb-email").val();
            if (email != "")
                html = "<a href='mailto:" + email + "'>" + getSelectedText() + "</a>"
        }

        if (html) {
            insertHTML(html);
        }

        overlay_2.close();
        return false;
    });

    $("#insert-image").live("click", function(e) {
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
        overlay_2.close();
        return false;
    })

    $("a.fb-obj").live("click", function() {
        var url = $(this).attr("href");
        var id = $("#obj-id").attr("data");
        $.get(url + "&current_id=" + id, function(data) {
            $("#overlay-2 .content").html(data);
        });
        return false;
    });
});