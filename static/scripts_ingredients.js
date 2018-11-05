// Extend function to set checkobxes to default
let old_func = form_set_new;
form_set_new = function(form){
    old_func(form);

    var checkboxes = $(form).find('input[type=checkbox]');
    for ( let x of checkboxes ) {
        var default_val;
        try {
            default_val = $(x).data("default");
        } catch (err) {
            default_val = false;
        }
        $(x).prop("checked", default_val);
    }
};

function form_set_edit(form, db_id, data=null) {
    if ( data ) {
        // Set string input fields
        for ( let key in data ) {
            if ( typeof(data[key]) != "object" ) {
                $(form).find("[id$=" + key + "]").val(data[key]);
            }
        }

        // Set category
        $(form).find("#select-category").val(data["category"]["db_id"]);

        // Set allergies
        for ( a of data["allergies"]) {
            var a_id = "#check-allergy_" + a["db_id"];
            $(form).find(a_id).prop("checked", true);
        }
    } else {
        form_set_new(form);
        fetch_object(obj_type, db_id, function(obj) {
            form_set_edit(form, db_id, obj);
        });
    }
}