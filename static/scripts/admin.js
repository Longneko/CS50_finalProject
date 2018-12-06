// function fetch_object is imported from fetch.js via template

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
    case "users":
        obj_type = "user";
        break;
}

// Set form element to default state based on its type and data-default if provided
function set_default(element) {
    var type;
    switch($(element).prop('nodeName')) {
        case "SELECT":
            type = "select";
            break
        case "TEXTAREA":
            type = "textarea";
            break
        case "IMG":
            type = "img";
            break
        case "INPUT":
            type = $(element).attr("type");
            break
        default:
            return false;
    }

    var default_val;
    try {
        default_val = $(element).data("default");
    } catch (err) {
        default_val = "";
    }

    if ( ["select", "textarea", "text", "number", "email", "url", "file"].includes(type) ) {
        $(element).val(default_val);
    }
    if ( type == "checkbox" ) {
        $(element).prop("checked", Boolean(default_val));
    }
    if ( type == "img" ) {
        if ( default_val ) {
            $(element).prop("src", default_val);
        }
    }
}

// Sets basic form values to default from data-default if possible
function form_set_new(form_id) {
    $("#modal-label-" + form_id).text("New element");

    var form_elements = $("[form="+ form_id + "]");

    set_default(form_elements.filter("[name=id]"));
    set_default(form_elements.filter("[name=name]"));
}

// Sets form values to those of the object under editing
function form_set_edit(form_id, id, data=null) {
    $("#modal-label-" + form_id).text("Edit element");

    if ( data ) {
        var form_elements = $("[form="+ form_id + "]");

        form_elements.filter("[name=id]").val(data["id"]);
        form_elements.filter("[name=name]").val(data["name"]);
    } else {
        form_set_new(form_id);
        fetch_object(obj_type, id, function(obj) {
            form_set_edit(form_id, id, obj);
        });
    }
}


$(document).ready(function() {
    // On new popluate the form with default values
    $("[data-target^='#modal-form_write']:not([data-obj_id])").click(function() {
        var modal_id = $(this).data("target");
        var form_id = $(modal_id).find("form").attr("id")
        form_set_new(form_id);
    });

    // On edit popluate form with values of the entry under editing
    $("[data-target^='#modal-form_write']").click(function() {
        var modal_id = $(this).data("target");
        var form_id = $(modal_id).find("form").attr("id")

        var id = $(this).data("obj_id");
        form_set_edit(form_id, id);
    });

    // On remove popluate form with id of the entry to be removed
    $("[data-target^='#modal-form_remove']").click(function() {
        var modal_id = $(this).data("target");
        var form_id = $(modal_id).find("form").attr("id")
        var obj_id = $(this).data("obj_id")

        $("[form=" + form_id + "][name=id]").val(obj_id)

        // var id = $(this).data("obj_id");
        // form_set_edit(form_id, id);
    });

    // Focus on Name field when modal window is shown
    $("#modal-form").on("shown.bs.modal", function() {
        $(this).find("input[name=name]").focus();
    });
});