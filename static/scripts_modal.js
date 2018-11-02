// Sets basic form values to default from data-default if possible
function form_set_new(form){
    var texts = $(form).find('input[type=text]');
    var selects = $(form).find('select');
    for ( x of $.merge(texts, selects) ) {
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
function form_set_edit(form, data){
    for ( key in data ) {
        $(form).find("[id$=" + key + "]").val(data[key]);
    }
}

$(document).ready(function(){
    // On new popluate form with default values
    $(".trigger-form-new").click(function(){
        var modal_id = $(this).data("target");
        var form = $(modal_id).find("form");
        form_set_new(form);
    });

    // On edit popluate form with values of the entry under editing
    $(".trigger-form-edit").click(function(){
        var modal_id = $(this).data("target");
        var form = $(modal_id).find("form");

        var db_id = $(this).data("db_id");
        var name = $("#td_name_" + db_id).text().trim();
        var data = {
            "db_id": db_id,
            "name": name
        };

        form_set_edit(form, data);
    });

    // Focus on Name field when modal window is shown
    $("#modal-form").on("shown.bs.modal", function(){
        $("#form-name").focus();
    });
});
