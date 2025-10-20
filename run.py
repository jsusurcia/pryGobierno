from app import create_app
from app.config import configurations

config = configurations['development']
app = create_app(config)

if __name__ == '__main__':
    app.run(debug=True)