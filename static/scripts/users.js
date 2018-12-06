// Extend function to set checkobxes and category to default
let old_form_set_new = form_set_new;
form_set_new = function(form_id){
    old_form_set_new(form_id);

    var form_elements = $("[form="+ form_id + "]");
    var is_admin = form_elements.filter('[name=is_admin]');

    set_default(is_admin);
};

// Extend function to set checkobxes and category based on fetched object
let old_form_set_edit = form_set_edit;
form_set_edit = function(form_id, id, data=null) {
    old_form_set_edit(form_id, id, data);

    if (data) {
        var form_elements = $("[form="+ form_id + "]");
        var is_admin = form_elements.filter("[name=is_admin]");

        is_admin.get(0).checked = data["is_admin"]
    }
};
