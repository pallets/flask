(() => {
'use strict';

function buildGraph(response) {
  const cop = response.cop;
  const cops = response.cops;
  const timestamp = response.timestamp;


  var chart = c3.generate({
      data: {
          x: 'x',
          columns: [
              timestamp,
              cop,
              cops
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
  //This returns JSON
  const resp = axios.get('http://localhost:5000/api')
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

