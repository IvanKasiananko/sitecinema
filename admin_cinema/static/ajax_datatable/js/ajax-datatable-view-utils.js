
/*!
 * Utils for Django Ajax Datatable View integration
 * https://github.com/morlandi/django-ajax-datatable
 */
var AjaxDatatableViewUtils = {
    initialize_table: function($table, ajax_url, datatable_options, extra_data) {
        var options = $.extend(true, {
            processing: true,
            serverSide: true,
            ajax: {
                url: ajax_url,
                type: 'GET',
                data: function(d) {
                    if (extra_data) {
                        $.each(extra_data, function(k, v) {
                            d[k] = v;
                        });
                    }
                }
            }
        }, datatable_options);

        $table.DataTable(options);
    }
};
