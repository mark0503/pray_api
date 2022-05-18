from setuptools import setup


setup(
    name="pray_app",
    version='0.0.1',
    author="pers.mrk",
    install_requires=[
      'fastapi==0.70.0',
      'uvicorn==0.15.0',
      'SQLAlchemy==1.4.26',
      'requests==2.26.0',
      'python-jose==3.3.0'
    ],
    scripts=['app/main.py', 'script/create_db.py']

)
