// Show default for a broken image
function img_error(e) {
    $(e).on("error", null); // to avoid infinite loop if default is not available
    $(e).prop("src", $(e).data("default"));
}

// Change img src to a new file within the same directory
function img_change_file(img, new_name, new_ext=null) {
    var old_name = $(img).prop("src").split("/").pop();
    var old_ext = "." + old_name.split(".").pop();
    var new_src = $(img).prop("src").replace(old_name, new_name + (new_ext ? new_ext : old_ext));

    $(img).prop("src", new_src);
}

// Get object from DB asynchronously and execute provided func on success
function fetch_object(obj_type, id, success) {
    var params = {
        "obj_type": obj_type,
        "id": id,
    }
    var url = window.location.origin + "/json"

    $.getJSON(url, params, function(data) {
        return success(data);
    });
}
