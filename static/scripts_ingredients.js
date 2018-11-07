// Extend function to set checkobxes and category to default
let old_form_set_new = form_set_new;
form_set_new = function(form_id){
    old_form_set_new(form_id);

    var form_elements = $("[form="+ form_id + "]");
    var category_select = set_default(form_elements.filter("[name=category_id]"));
    var checkboxes = form_elements.filter('input[type=checkbox]');

    set_default(category_select);
    for ( let c of checkboxes ) {
        set_default(c);
    }
};

// Extend function to set checkobxes and category based on fetched object
let old_form_set_edit = form_set_edit;
form_set_edit = function(form_id, db_id, data=null) {
    old_form_set_edit(form_id, db_id, data);

    if (data) {
        var form_elements = $("[form="+ form_id + "]");

        // Set category
        form_elements.filter("[name=category_id]").val(data["category"]["db_id"]);

        // Set allergies
        for ( a of data["allergies"]) {
            var a_id = "#check-allergy_" + a["db_id"];
            form_elements.filter(a_id).prop("checked", true);
        }
    }
};
