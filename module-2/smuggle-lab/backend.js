/**
 * Backend "raw" — usa o módulo http nativo, que respeita Content-Length quando
 * Transfer-Encoding está presente mas formatado de forma ambígua (sem chunked
 * conforme RFC). Dá margem para TE.CL desync no contexto deste lab didático.
 */
const http = require("http");

const sessions = new Map(); // toy: cookie -> data

const server = http.createServer((req, res) => {
  let body = "";
  req.on("data", c => (body += c));
  req.on("end", () => {
    // Log para você ver no `docker logs smuggle-back` o que chegou
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url} headers=${JSON.stringify(req.headers)} body=${JSON.stringify(body)}`);

    if (req.url === "/admin") {
      const xs = req.headers["x-smuggled"];
      res.writeHead(200, { "Content-Type": "text/plain" });
      return res.end(xs ? `ADMIN_OK smuggled=${xs}\n` : "forbidden\n");
    }

    res.writeHead(200, { "Content-Type": "text/html" });
    res.end("<h1>ACME backend</h1>\n");
  });
});

server.listen(8081, () => console.log("backend on :8081"));
