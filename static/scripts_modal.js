// Get page name
var path = window.location.pathname;
var page = path.split("/").pop();

// Set type of object to be edited in forms
var obj_type;
switch(page) {
    case "allergies":
        obj_type = "allergy";
        break;
    case "ingredient_categories":
        obj_type = "ingredient_category";
        break;
    case "ingredients":
        obj_type = "ingredient";
        break;
    case "recipes":
        obj_type = "recipe";
        break;
}

// Get object from DB asynchronously and execute provided func on success
function fetch_object(obj_type, db_id, success) {
    var params = {
        "obj_type": obj_type,
        "db_id": db_id,
    }
    var url = window.location.origin + "/json"

    $.getJSON(url, params, function(data) {
        return success(data);
    });
}

// Sets basic form values to default from data-default if possible
function form_set_new(form) {
    var texts = $(form).find('input[type=text]');
    var selects = $(form).find('select');
    for ( let x of $.merge(texts, selects) ) {
        var default_val;
        try {
            default_val = $(x).data("default");
        } catch (err) {
            default_val = "";
        }
        $(x).val(default_val);
    }
}

// Sets form values to those of the object under editing
function form_set_edit(form, db_id, data=null) {
    if ( data ) {
        for ( let key in data ) {
            $(form).find("[id$=" + key + "]").val(data[key]);
        }
    } else {
        form_set_new(form);
        fetch_object(obj_type, db_id, function(obj) {
            form_set_edit(form, db_id, obj);
        });
    }
}


$(document).ready(function() {
    // On new popluate form with default values
    $(".trigger-form-new").click(function() {
        var modal_id = $(this).data("target");
        var form = $(modal_id).find("form");
        form_set_new(form);
    });

    // On edit popluate form with values of the entry under editing
    $(".trigger-form-edit").click(function() {
        var modal_id = $(this).data("target");
        var form = $(modal_id).find("form");

        var db_id = $(this).data("db_id");
        form_set_edit(form, db_id);
    });

    // Focus on Name field when modal window is shown
    $("#modal-form").on("shown.bs.modal", function() {
        $("#form-name").focus();
    });
});
