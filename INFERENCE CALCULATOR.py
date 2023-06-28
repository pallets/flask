from flask import Flask, request, jsonify
import numpy as np
from flask import Flask, request, render_template
import numpy as np

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    result = None
    if request.method == 'POST':
        # Get the comma-separated string, split by commas, and convert to integer
        s_data = np.array([int(i) for i in request.form.get('s_data', '').split(',') if i])
        ns_data = np.array([int(i) for i in request.form.get('ns_data', '').split(',') if i])

        total = sum(s_data) + sum(ns_data)

        # Calculate marginal probabilities
        marginal_prob_s = s_data / total
        marginal_prob_ns = ns_data / total

        # Calculate joint probabilities
        joint_prob = np.outer(marginal_prob_s, marginal_prob_ns)

        # Calculate likelihoods
        posterior_s = s_data / sum(s_data)
        posterior_ns = ns_data / sum(ns_data)

        #likelihood
        likelihood_s = marginal_prob_s
        likelihood_ns = marginal_prob_ns

        # Return results as dictionary
        result = {
            "JOINT PROBABILITY": joint_prob.tolist(),
            "MARGINAL PROBABILITY_S": marginal_prob_s.tolist(),
            "MARGINAL PROBABILITY_NS": marginal_prob_ns.tolist(),
            "LIKELIHOOD_S": likelihood_s.tolist(),
            "LIKELIHOOD_NS": likelihood_ns.tolist(),
            "POSTERIOR_S": posterior_s.tolist(),
            "POSTERIOR_NS": posterior_ns.tolist()
        }

    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
