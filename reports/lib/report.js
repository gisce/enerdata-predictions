function parseCSV(file) {
    var csv = $.ajax({
        type: 'get',
        url: file,
        dataType: 'plaintext',
        context: document.body,
        global: false,
        async:false,
        success: function(data) {
            return data;
        }
    }).responseText;
    return (csv);
};


function processData(file) {

    var allText = parseCSV(file);

    var allTextLines = allText.split(/\r\n|\n/);
    var entries = [];
    var header = true;

    $.each(allTextLines, function(n, elem) {
        if (header) return !(header=false);

        entries.push(elem.split(";"));
    });
    return entries;


}

