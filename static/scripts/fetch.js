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
