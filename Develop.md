# Develop axioms-cli

## Clone the repostiroy

```
git clone https://github.com/axioms-io/sample-python-cli
cd sample-python-cli
```

## Setup
Create virtualenv,

```
python3 -m venv venv
```

Then activate virtualenv and install requirements,

```
source venv/bin/activate
pip install -r requirements-dev.txt
```

## Working in development mode
Add following in `requirements.txt` file

```
-e /path/to/sample-python-cli
```

or

```
pip install -e /path/to/sample-python-cli
```

or

```
pip install -e .
```