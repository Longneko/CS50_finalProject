// Extend function to set checkobxes to default
let old_func = form_set_new;
form_set_new = function(form){
    old_func(form);

    var checkboxes = $(form).find('input[type=checkbox]');
    for ( x of checkboxes ) {
        var default_val;
        try {
            default_val = $(x).data("default");
        } catch (err) {
            default_val = false;
        }
        $(x).prop("checked", default_val);
    }
};

// TODO set_edit extend to get category and allergies