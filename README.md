# My Flask Project

This is a simple Flask web application that demonstrates the basic structure and functionality of a Flask project.

## Project Structure

```
my-flask-project
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   └── templates
│       └── index.html
│   └── static
│       └── css
│           └── style.css
├── tests
│   └── test_app.py
├── config.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd my-flask-project
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, use the following command:
```
flask run
```

Visit `http://127.0.0.1:5000` in your web browser to view the application.

## Running Tests

To run the tests, execute:
```
pytest tests/test_app.py
```

## License

This project is licensed under the MIT License.