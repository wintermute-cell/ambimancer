#!/bin/sh
cd client
npm run --silent dev & disown
cd ..
flask run
