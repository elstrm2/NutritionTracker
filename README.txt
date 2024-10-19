Installation on Linux

1. sudo apt update
2. sudo apt dist-upgrade -y
3. sudo apt autoremove -y
4. sudo apt autoclean
5. sudo reboot
6. sudo apt install python3 python3-pip
7. sudo apt update 
8. sudo apt install redis-server -y
9. sudo systemctl status redis
10. redis-cli ping
11. sudo systemctl enable redis-server
12. sudo systemctl restart redis-server
13. sudo systemctl status redis-server
14. redis-cli ping
15. sudo apt update
16. sudo apt install postgresql postgresql-contrib -y
17. sudo systemctl status postgresql
18. sudo systemctl enable postgresql
19. sudo systemctl restart postgresql
20. sudo systemctl status postgresql
21. sudo -i -u postgres
22. psql
23. ALTER USER postgres WITH PASSWORD 'PASSWORD';
24. sudo nano /etc/postgresql/VERSION/main/pg_hba.conf (if local password is needed)
25. change 'local all postgres' to 'local all md5' (if local password is needed)
26. sudo systemctl restart postgresql (if local password is needed)
27. psql -U postgres (if local password is needed)
28. on windows: scp -r "folderRoot" root@IP:/root/
29. pip install -r requirements.txt
30. sudo apt update
31. sudo apt install screen
32. screen -S bot_session
33. bash create_db.sh
34. bash run_bot.sh
35. Ctrl + A, then D
36. screen -ls
37. screen -r bot_session
38. Ctrl + C or exit to exit