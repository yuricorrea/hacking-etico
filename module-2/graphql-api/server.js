/**
 * ACME GraphQL API — intencionalmente vulnerável.
 * Vulnerabilidades plantadas:
 *   - JWT HS256 com segredo "secret" (rockyou)
 *   - alg:none aceito (vulnerabilidade clássica)
 *   - Introspection habilitada em produção
 *   - BOLA: order(id) não checa user
 *   - Race condition em redeem(code)
 *   - SSRF via mutation proxyFetch(url)
 */
const express = require("express");
const { graphqlHTTP } = require("express-graphql");
const { buildSchema } = require("graphql");
const jwt = require("jsonwebtoken");
const http = require("http");

const SECRET = "secret"; // 🔥 senha em rockyou

// "Banco" em memória
const users = [
  { id: 1, email: "alice@acme.local", password: "alice2026", role: "user", balance: 100 },
  { id: 2, email: "bob@acme.local",   password: "bob123",     role: "user", balance: 50  },
  { id: 3, email: "admin@acme.local", password: "S3cur3!Adm", role: "admin", balance: 9999 },
];
const orders = [
  { id: 1, userId: 3, total: 4200, item: "Vault" },
  { id: 2, userId: 1, total: 19,   item: "Mug"   },
  { id: 3, userId: 2, total: 49,   item: "Hoodie" },
];
const coupons = { FREE10: { discount: 10, redeemedBy: new Set() } };

const schema = buildSchema(`
  type User { id: Int! email: String! role: String! balance: Int! }
  type Order { id: Int! total: Int! item: String! user: User! }
  type AuthPayload { token: String! user: User! }
  type RedeemPayload { balance: Int! }

  type Query {
    me: User
    order(id: Int!): Order
    orders: [Order!]!
  }

  type Mutation {
    login(email: String!, password: String!): AuthPayload
    redeem(code: String!): RedeemPayload
    proxyFetch(url: String!): String
  }
`);

function decode(token) {
  if (!token) return null;
  try {
    // Decodifica SEM verificar primeiro (para suportar alg:none vulnerável)
    const [h, p] = token.split(".");
    const header  = JSON.parse(Buffer.from(h, "base64").toString());
    const payload = JSON.parse(Buffer.from(p, "base64").toString());
    if (header.alg === "none") return payload; // 🔥 vuln
    return jwt.verify(token, SECRET, { algorithms: ["HS256"] });
  } catch (e) {
    return null;
  }
}

function ctxFromReq(req) {
  const auth = req.headers.authorization || "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : null;
  const claims = decode(token);
  const user = claims ? users.find(u => u.id === claims.sub) : null;
  return { claims, user };
}

const root = {
  me: (_, req) => ctxFromReq(req).user,

  // 🔥 BOLA: não filtra por user
  order: ({ id }, req) => {
    const o = orders.find(x => x.id === id);
    if (!o) return null;
    return { ...o, user: users.find(u => u.id === o.userId) };
  },

  orders: () => orders.map(o => ({ ...o, user: users.find(u => u.id === o.userId) })),

  login: ({ email, password }) => {
    const u = users.find(x => x.email === email && x.password === password);
    if (!u) throw new Error("invalid creds");
    const token = jwt.sign({ sub: u.id, role: u.role }, SECRET, { algorithm: "HS256" });
    return { token, user: u };
  },

  // 🔥 Race: leitura/checagem/escrita não atômica
  redeem: async ({ code }, req) => {
    const ctx = ctxFromReq(req);
    if (!ctx.user) throw new Error("auth required");
    const c = coupons[code];
    if (!c) throw new Error("invalid code");

    // Janela artificial para a race ser fácil de demonstrar
    const already = c.redeemedBy.has(ctx.user.id);
    await new Promise(r => setTimeout(r, 50));
    if (already) throw new Error("already redeemed");
    c.redeemedBy.add(ctx.user.id);
    ctx.user.balance += c.discount;

    return { balance: ctx.user.balance };
  },

  // 🔥 SSRF — exige role admin (mas é trivial forjar via JWT secret fraco)
  proxyFetch: ({ url }, req) => {
    const ctx = ctxFromReq(req);
    if (!ctx.claims || ctx.claims.role !== "admin") throw new Error("admin only");
    return new Promise((resolve, reject) => {
      http.get(url, (res) => {
        let data = "";
        res.on("data", chunk => (data += chunk));
        res.on("end", () => resolve(data));
      }).on("error", reject);
    });
  },
};

const app = express();
app.get("/healthz", (_, res) => res.send("ok"));

app.use("/graphql", graphqlHTTP((req) => ({
  schema,
  rootValue: root,
  context: req,
  graphiql: true,    // 🔥 GUI em prod
})));

app.listen(4000, () => console.log("GraphQL API on :4000"));
