// ===============================
// IriLine Collective News Server
// - Serves static files from /public
// - Provides APIs:
//    GET /api/news?offset=0&limit=12
//    GET /api/article?id=hero_001
//    GET /api/ads
// ===============================

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <unordered_map>

#include "third_party/httplib.h"
#include "third_party/json.hpp"

using json = nlohmann::json;

static std::string read_file(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) return "";
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

static std::string mime_type(const std::string& path) {
  auto dot = path.find_last_of('.');
  if (dot == std::string::npos) return "application/octet-stream";
  std::string ext = path.substr(dot + 1);

  static std::unordered_map<std::string, std::string> m = {
      {"html", "text/html; charset=utf-8"},
      {"css", "text/css; charset=utf-8"},
      {"js", "application/javascript; charset=utf-8"},
      {"png", "image/png"},
      {"jpg", "image/jpeg"},
      {"jpeg", "image/jpeg"},
      {"svg", "image/svg+xml"},
      {"ico", "image/x-icon"},
      {"json", "application/json; charset=utf-8"},
  };
  if (m.count(ext)) return m[ext];
  return "application/octet-stream";
}

static json load_json(const std::string& path) {
  std::string s = read_file(path);
  if (s.empty()) return json::object();
  try {
    return json::parse(s);
  } catch (...) {
    return json::object();
  }
}

int main() {
  const std::string PUBLIC_DIR = "./public";
  const std::string NEWS_PATH  = "./data/news.json";
  const std::string ADS_PATH   = "./data/ads.json";

  httplib::Server svr;

  // -------------------------------
  // STATIC FILES
  // -------------------------------
  svr.Get(R"(/(.*))", [&](const httplib::Request& req, httplib::Response& res) {
    std::string target = req.matches[1];

    // API routes handled below; skip them here
    if (target.rfind("api/", 0) == 0) {
      res.status = 404;
      res.set_content("Not Found", "text/plain");
      return;
    }

    if (target.empty()) target = "index.html";

    // Basic directory traversal protection
    if (target.find("..") != std::string::npos) {
      res.status = 400;
      res.set_content("Bad Request", "text/plain");
      return;
    }

    std::string path = PUBLIC_DIR + "/" + target;
    std::string body = read_file(path);

    if (body.empty()) {
      res.status = 404;
      res.set_content("Not Found", "text/plain");
      return;
    }

    res.set_content(body, mime_type(path));
  });

  // -------------------------------
  // API: GET /api/news?offset=0&limit=12
  // returns array of articles (for cards + ticker)
  // -------------------------------
  svr.Get("/api/news", [&](const httplib::Request& req, httplib::Response& res) {
    json db = load_json(NEWS_PATH);
    if (!db.contains("articles") || !db["articles"].is_array()) {
      res.status = 500;
      res.set_content(R"({"error":"news.json missing articles[]"})", "application/json");
      return;
    }

    int offset = 0;
    int limit  = 12;

    if (req.has_param("offset")) offset = std::max(0, std::stoi(req.get_param_value("offset")));
    if (req.has_param("limit"))  limit  = std::max(1, std::stoi(req.get_param_value("limit")));

    auto& arr = db["articles"];

    json out = json::array();
    for (int i = offset; i < (int)arr.size() && (int)out.size() < limit; i++) {
      out.push_back(arr[i]);
    }

    res.set_content(out.dump(), "application/json; charset=utf-8");
  });

  // -------------------------------
  // API: GET /api/article?id=...
  // returns one full article
  // -------------------------------
  svr.Get("/api/article", [&](const httplib::Request& req, httplib::Response& res) {
    if (!req.has_param("id")) {
      res.status = 400;
      res.set_content(R"({"error":"missing id"})", "application/json");
      return;
    }
    std::string id = req.get_param_value("id");

    json db = load_json(NEWS_PATH);
    if (!db.contains("articles") || !db["articles"].is_array()) {
      res.status = 500;
      res.set_content(R"({"error":"news.json missing articles[]"})", "application/json");
      return;
    }

    for (auto& a : db["articles"]) {
      if (a.contains("id") && a["id"].get<std::string>() == id) {
        res.set_content(a.dump(), "application/json; charset=utf-8");
        return;
      }
    }

    res.status = 404;
    res.set_content(R"({"error":"article not found"})", "application/json");
  });

  // -------------------------------
  // API: GET /api/ads
  // returns ad blocks
  // -------------------------------
  svr.Get("/api/ads", [&](const httplib::Request& req, httplib::Response& res) {
    json ads = load_json(ADS_PATH);
    res.set_content(ads.dump(), "application/json; charset=utf-8");
  });

  std::cout << "IriLine Collective server running:\n";
  std::cout << "  http://localhost:8080\n";
  svr.listen("0.0.0.0", 8080);
  return 0;
}

