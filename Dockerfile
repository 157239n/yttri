FROM ubuntu:latest
WORKDIR /root
ENV PATH=/root/.local/bin:$PATH
RUN apt update && apt install -y git vim curl htop net-tools python3 python-is-python3 libmagic1 && curl vim.kelvinho.org | bash && curl -Ls https://astral.sh/uv/install.sh | bash
RUN uv venv env1 && echo "\nsource /root/.bashenv\n" >> /root/.bashrc && cat <<EOF >/root/.bashenv
    export PATH="$PATH:/root/.local/bin";
    source /root/env1/bin/activate
    function help() { echo ""; echo "Commands: ";
        echo "- run: run the application, with auto reloading on file change"
        echo "- runOld: run the application, while loop with bare python, does not auto reload, worst case scenario running"
        echo "- kill: kills the running application"
        echo "- update: updates the k1lib and aigu libraries"; echo ""; }
    function run() { watchfiles --filter python --sigint-timeout 2 'python main.py'; }
    function runOld() { while true; do python main.py >/dev/null 2>&1; done; }
    function kill() { pkill watchfiles; pkill python; }
    function update() { uv pip install --force-reinstall --extra-index-url http://172.30.6.100:3141/ --trusted-host 172.30.6.100 aigu k1lib; }
EOF
RUN . /root/env1/bin/activate && uv pip install watchfiles flask requests unidecode pycryptodome bcrypt python-magic
RUN . /root/env1/bin/activate && uv pip install --force-reinstall --extra-index-url http://172.30.6.100:3141/ --trusted-host 172.30.6.100 aigu mpld3 openmeteo_requests && echo a1
WORKDIR /code
CMD ["./startup"]



