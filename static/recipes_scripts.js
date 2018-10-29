const ING_BADGE_ID_PREFIX = "ing_badge_";
const ING_BADGE_CSS_CLASS = "badge badge-primary ml-1 mr-1";

// Array of Content objects for new recipe
let contents= [];

$(document).ready(function(){
    // Adds new content to contents array for the new recipe form
    $("#contents_add").click(function(){
        var ingredient_id = $("#ingredient_select").val()
        var amount = $("#amount").val()
        var units = $("#units").val()

        // Validate ingredient id and amount
        if ( !ingredient_id ) {
            $("#ingredient_select").focus();
            return;
        }
        if ( !(parseInt(amount) >=0) ) {
            $("#amount").focus();
            return;
        }

        // remove previously added identical ingredients
        var index = -1;
        for ( var i = 0; i < contents.length; i++ ) {
            if ( parseInt(contents[i]["ingredient_id"]) == ingredient_id) {
                index = i;
            }
        }
        if ( index > -1 ) {
            contents.splice(index, 1);
            $("#" + ING_BADGE_ID_PREFIX + ingredient_id).remove();
        }

        // Add ingredient badge to the ingredients lsit div
        var ingredient_name = $("#ingredient_select option:selected").text()
        $("#added_contents").append("<span class=\""+ ING_BADGE_CSS_CLASS + "\" id=\"" + ING_BADGE_ID_PREFIX + ingredient_id + "\">"
                                  + ingredient_name + ": " + amount + " " + units
                                  + "</span>"
        );

        // Add content to the contents list
        contents.push({
            ingredient_id: ingredient_id,
            amount: amount,
            units: units
        });

        console.log(contents);

        // Reset input field values
        $("#ingredient_select").val(0);
        $("#amount").val("");
        $("#units").val("");
    });


    $("#recipe_new").submit(function() {
        $("#contents").val(JSON.stringify(contents))
    });
});
