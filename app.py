from flask import Flask, render_template, request, session, url_for, redirect
import pickle
import datetime
from matplotlib import pyplot
import numpy as np
from sklearn.linear_model import LinearRegression

def load_obj(datatype):
    with open(f"{datatype}" + '.pkl', 'rb') as f:
        return pickle.load(f)


class Wine:
    quantitative_attributes = ['Sg', 'Brix', 'Ph', 'Temp', 'Sulphite', 'Notes']
    qualitative_attributes = ['Clarity', 'Aroma', 'Body', 'Color', 'Flavor', 'Sugar', 'Tannin', 'General Quality']
    S02 = [np.array([2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0]),
           np.array([11, 13, 16, 21, 26, 32, 40, 50, 63, 79, 99, 125])]

    def __init__(self, blend, props={}):
        self.blend = blend
        self.trait_hist = {}
        self.properties = {prop: val for prop, val in props.items()}

    def SO2_interp(self, current_date):
        ph = self.trait_hist[current_date].get('Ph', 0)
        model = LinearRegression()
        model.fit(self.S02[0].reshape(-1, 1), self.S02[1].reshape(-1, 1))
        return str(round(model.predict([[ph]])[0][0], 2))

    def abv(self, current_date):
        return str((float(float(self.properties['start_sg'])-self.trait_hist[current_date]['Sg']))*131.25)

    @property
    def attributes(self):
        return self.quantitative_attributes+self.qualitative_attributes


app = Flask(__name__)
app.secret_key = 'dev'


@app.route('/')
def home():
    temp = load_obj('open_wines')
    return render_template('index.html', current_wines=temp)

@app.route('/view/<name>', methods=["POST", "GET"])
def view(name):
    wines = load_obj('shelf')
    if request.method == 'POST':
        session['new_obs'].update(request.form)
        for val in wines[name].attributes:
            if val not in session['new_obs']:
                session['new_obs'][val] = ''
        wines[name].trait_hist[datetime.datetime.today()] = session['new_obs']
        pick_out = open(f"shelf.pkl", "wb")
        pickle.dump(wines, pick_out, pickle.HIGHEST_PROTOCOL)
        pick_out.close()
    return render_template('view.html', wine=wines.get(name, None), name=name)

@app.route('/new', methods=['POST', 'GET'])
def new():
    if request.method == 'POST':
        temp = load_obj('shelf')
        res = dict(request.form)
        res.pop('button')
        nw = Wine(res.pop('Blend_Name'), res)
        temp[nw.blend] = nw
        # pick_out = open(f"shelf.pkl", "wb")
        # pickle.dump(nw, pick_out, pickle.HIGHEST_PROTOCOL)
        # pick_out.close()
    return render_template('new.html')

@app.route('/graph', methods=['POST', 'GET'])
def graph_select():
    if request.method == 'POST':
        return redirect(url_for('graph', selection=request.form['gs']))
    return render_template('graph_selection.html', attributes=Wine.quantitative_attributes+Wine.qualitative_attributes)

@app.route('/graph/<selection>')
def graph(selection):
    pyplot.close()
    wines = load_obj('shelf')
    x = [[val for val in wines[w].trait_hist.keys()] for w in wines.keys()]
    y = [[val[selection] for val in wines[w].trait_hist.values()] for w in wines.keys()]
    [pyplot.plot(x[ind], y[ind], label=key) for ind, key in enumerate(list(wines.keys()))]
    pyplot.xlabel('Date')
    pyplot.ylabel(selection)
    pyplot.legend(loc="upper left")
    pyplot.savefig(f'./static/{selection}.png')
    return render_template('graph.html', img_path=f'/static/{selection}.png')


@app.route('/update/quant/<name>', methods=['POST', 'GET'])
def update_quant(name):
    wine = load_obj('shelf').get(name, None)
    if request.method=='POST':
        session['new_obs'] = dict(request.form)
        return render_template('update_qual.html', attributes=wine.qualitative_attributes, name=name)
    return render_template('update_quant.html', attributes=wine.quantitative_attributes, name=name)

@app.route('/update/qual/<name>', methods=['POST', 'GET'])
def update_qual(name):
    wine = load_obj('shelf').get(name, None)
    return render_template('update_qual.html', attributes=wine.qualitative_attributes, name=name)


if __name__ == "__main__":
    app.run(debug=True)