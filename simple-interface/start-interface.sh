#!/bin/bash
  
set -m

cd ./server/ && streamlit run ./app.py &

cd ./frontend/ && HOST=localhost npm start 
 
fg %1