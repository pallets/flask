
(() => {

function buildGraph() {
'use strict';

  var chart = c3.generate({
      data: {
          x: 'x',
  //        xFormat: '%Y%m%d', // 'xFormat' can be used as custom format of 'x'
          columns: [
              ['x', '2013-01-01', '2013-01-02', '2013-01-03', '2013-01-04', '2013-01-05', '2013-01-06'],
  //            ['x', '20130101', '20130102', '20130103', '20130104', '20130105', '20130106'],
              ['data1', 30, 200, 100, 400, 150, 250],
              ['data2', 130, 340, 200, 500, 250, 350]
          ]
      },
      axis: {
          x: {
              type: 'timeseries',
              tick: {
                  format: '%Y-%m-%d'
              }
          }
      }
  });
}

function getArticles() {
  const resp = axios.get('')
    .then(function (response) {
      console.log(response);
    })
    .catch(function (error) {
      console.log(error);
    });

  // parse
  // return parsed response
}


buildGraph(getArticles());

})();

