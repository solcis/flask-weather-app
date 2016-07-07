$(function() {
	// configure typeahead
	$('#q').typeahead({
		autoselect: true,
		highlight: true,
		minLength: 1,
	},
	{
		source: search,
		templates: {
			suggestion: _.template("<p><%- city %>, <%- country_code %></p>"),
		}
	});	
});

/**
 * Searches database for typeahead's suggestions.
 */
function search(q, cb) {
	var parameters = {
		city: q,
	};
	$.getJSON('http://localhost:5000/search/', parameters)
	.done(function(data, textStatus, jqXHR) {
		cb(data);
	})
	.fail(function(jqXHR, textStatus, errorThrown) {
		console.log(errorThrown.toString());
	});
}