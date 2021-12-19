#!/bin/sh
cd client
npm run dev &
cd ..
flask run
