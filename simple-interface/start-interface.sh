#!/bin/bash
  
set -m

cd ./server/ && streamlit run ./app.py &

cd ./frontend/ && npm start 
 
fg %1
