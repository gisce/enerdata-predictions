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

    var text = parseCSV(file);

    var lines = text.split(/\r\n|\n/);
    var entries = [];
    var header = true;

    $.each(lines, function(n, elem) {
        if (header) return !(header=false);
        entries.push(elem.split(";"));
    });
    return entries;
}


$.urlParam = function(name){
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null){
       return "";
    }
    else{
       return results[1] || 0;
    }
}


var dataset = "hist/"+$.urlParam('dataset');

function get_hist () {

        var data_csv = processData(dataset + "index.csv");

        var historic = '<table class="table table-bordered table-striped"> <tbody> <tr><th>Data</th>'
            //+ <th>Període</th></tr>'
        ;

        $.each(data_csv, function (n, elem) {
            historic += "<tr><td><a href='javascript:create_chart(\"#execucio\", \""+ elem[0] + "\");'>"+elem[0]+"</a></td>";
           // historic += "<td>"+elem[1]+"</td></tr>";
        });

        return historic + "</tbody> </table>";

}

function create_chart(ON,quin) {

    var quinn = (quin)?quin:$.urlParam('dataset');
    dataset = "hist/"+ quinn;

    var data_csv = processData(dataset + "/past.csv");
    var data_csv_pred = processData(dataset + "/pred.csv");

    var chart;
    var data;


    nv.addGraph(function () {

        chart = nv.models.lineChart()
            .options({
                transitionDuration: 300,
                useInteractiveGuideline: true
            })
        ;

        chart.xAxis
            .showMaxMin(false)
            .axisLabel("Data")

            //.tickFormat(d3.format(',.1f'))
            .tickFormat(
                function (d) {
                    return d3.time.format('%d/%m %H:%M')(new Date(d))
                    //return d3.time.format('%d/%m %H:%M')(new Date(d))
                }
            )
            .staggerLabels(true)
        ;
        chart.yAxis
            .axisLabel('Energia (kw)')
            .showMaxMin(true)
            .tickFormat(function (d) {
                if (d == null) {
                    return 'N/A';
                }
                return d3.format(',.4f')(d);
            })
        ;
        data = dades(data_csv, data_csv_pred);


        d3.select(ON).append('svg')
            .datum(data)
            .call(chart);
        nv.utils.windowResize(chart.update);
        return chart;
        });


        function dades(data_csv, data_csv_prediccio) {
            var passat = [],
                prediccio = [];

            for (var i = 0; i < data_csv.length; i++) {

                passat.push({
                    x: new Date(data_csv[i][0], data_csv[i][1] - 1, data_csv[i][2], data_csv[i][3], 0),
                    y: data_csv[i][4]
                });
                prediccio.push({
                    x: new Date(data_csv_prediccio[i][0], data_csv_prediccio[i][1] - 1, data_csv_prediccio[i][2], data_csv_prediccio[i][3], 0),
                    y: Math.round(data_csv_prediccio[i][4])
                });
            }

            return [
                {
                    area: true,
                    values: passat,
                    key: "Passat",
                    color: "#ff7f0e",
                    strokeWidth: 2,
                    classed: 'dashed'
                },
                {
                    area: true,
                    values: prediccio,
                    key: "Predicció",
                    color: "#2ca02c",
                    strokeWidth: 2,
                    classed: 'dashed'
                }
            ];
        }
}
