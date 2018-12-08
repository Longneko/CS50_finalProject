// function img_change_file is imported from image.js via template

const ING_BADGE_ID_PREFIX = "contents-added-badge_";
const ING_BADGE_CSS_CLASS = "badge badge-primary ml-1 mr-1";
const BADGE_REMOVE_CHAR = "&#x274E;";

// Array of Content objects for recipe in editing
var form_contents = [];

// Extend function to set insturctions and contents to default
let old_form_set_new = form_set_new;
form_set_new = function(form_id){
    old_form_set_new(form_id);

    var form_elements = $("[form="+ form_id + "]");
    set_default(form_elements.filter("[id^=form-image-current]"));
    set_default(form_elements.filter("[name=instructions]"));
    set_default($("#contents-select-ingredient"));

    var ingredient_ids = form_contents.map(x => x["ingredient_id"]);
    for ( i of ingredient_ids ) {
        content_remove(form_contents, i);
    }

};

// Extend function to set insturctions and contents based on fetched object
let old_form_set_edit = form_set_edit;
form_set_edit = function(form_id, id, data=null) {
    old_form_set_edit(form_id, id, data);

    if ( data ) {
        var image =  $("[form="+ form_id + "]").filter("[id^=form-image-current]");
        // var image = $("#" + form_id);
        img_change_file(image, data["id"]);

        var instructions =  $("[form="+ form_id + "]").filter("[name=instructions]");
        instructions.val(data["instructions"]);

        // Set contents
        for ( c of data["contents"]) {
            var ingredient = {
                id: parseInt(c["ingredient"]["id"]),
                name: c["ingredient"]["name"],
            };
            var amount = parseFloat(c["amount"]);
            var units = c["units"];

            content_add(form_contents, ingredient, amount, units);
        }
    }
};


// Add new content to the list and reflect that in the interface
function content_add(list, ingredient, amount=0.0, units=null) {
    // Add ingredient badge to the ingredients list div
    $("#contents-added").append("<span class='"+ ING_BADGE_CSS_CLASS + "' id='" + ING_BADGE_ID_PREFIX + ingredient["id"] + "'>"
                                + ingredient["name"]
                                + ( amount ? ": " + amount : "" )
                                + ( units ? " " + units : "" )
                                + "<span class='action' id='contents-remove_" + ingredient["id"] + "' data-ingredient_id=" + ingredient["id"] + " aria-label='remove'> " + BADGE_REMOVE_CHAR + "</span>"
                                + "</span>"
    );

    // Binding the remove button function for the new content badge
    $("#contents-remove_" + ingredient["id"]).click(function() {
        var ingredient_id = parseInt($(this).data("ingredient_id"));
        content_remove(form_contents, ingredient_id);
    });

    // Add content to the contents list
    content = {
        ingredient_id: parseInt(ingredient["id"]),
        amount       : parseFloat(amount),
        units        : units ? units : null
    };
    list.push(content);
}

// Remove content specified by ingredient id from the list and reflect that in the interface
function content_remove(list, ingredient_id) {
    var index = -1;
    for ( var i = 0; i < list.length; i++ ) {
        if ( list[i]["ingredient_id"] == ingredient_id) {
            index = i;
        }
    }
    if ( index > -1 ) {
        list.splice(index, 1);
        $("#" + ING_BADGE_ID_PREFIX + ingredient_id).remove();
    }
}

$(document).ready(function() {
    // Disables image upload elements and clears selected file if delete is checked
    $("#form-image-delete").change(function() {
        var form_id = $(this).attr("form");
        var form_elements = $("[form="+ form_id + "]");

        if ( this.checked ) {
            set_default(form_elements.filter("[name=image]"));
            form_elements.filter("[id=form-image-upload-group]").hide("fast");
        } else {
            form_elements.filter("[id=form-image-upload-group]").show("fast");
        }
    });

    // Adds new content to contents array for the db_write form
    $("#contents-add").click(function() {
        var ingredient = {
            id: $("#contents-select-ingredient").val(),
            name : $("#contents-select-ingredient option:selected").text(),
        };
        var amount = parseFloat($("#contents-amount").val());
        var units = $("#contents-units").val();



        // Validate ingredient id and amount
        if ( !ingredient["id"] ) {
            $("#contents-select-ingredient").focus();
            return;
        }
        if ( !(parseFloat(amount) >=0) ) {
            $("#contents-amount").focus();
            return;
        }

        // Remove old content with the same ingredient if any and add the new one
        content_remove(form_contents, ingredient["id"]);
        content_add(form_contents, ingredient, amount, units);

        // Reset input field values
        $("#contents-select-ingredient").val(0);
        $("#contents-select-ingredient").focus();
        $("#contents-amount").val("");
        $("#contents-units").val("");

    });

    // Trigger 'Add' button press Enter key for content inputs
    $("[id|=contents]").filter("input").keyup(function(e) {
        if ( e.which == 13 ) {
            $("#contents-add").click();
        }
    });

    // Intercept form submit to attach contents data
    $("#form-db_write").submit(function(e) {
        var form_id = $(this).attr("id");

        $("[form="+ form_id + "]").filter("[name=contents]").val(JSON.stringify(form_contents));
    });
});
