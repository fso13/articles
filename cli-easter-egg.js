(function () {
  var CLICKS = 13;
  var SK = "talosThemeClicks";
  var shown = false;

  /** Подсказки к ⧚…⧛: data-cli-recovery-b64 / fetch */
  var RECOVERY_VNODE = "._____fffd.qbf";
  /** Диалог fso13/Jenny (общага, экраны): data-cli-nostalgia-b64 / fetch */
  var NOSTALGIA_VNODE = ".___bench~stk.log";

  var FILES = {
    "/home/guest/readme.txt":
      "Добро пожаловать в гостевую сессию.\nВведите help — список команд.\nПапка draft/ — черновики (не на главной): cd draft, ls, cat имя.md\n",
    "/home/guest/docs/note.txt":
      "Черновик: проверить логи перед выходом.\n",
    "/var/log/app.log":
      "2024-01-15T10:00:01Z INFO start\n2024-01-15T10:00:02Z WARN checksum\n2024-01-15T10:05:00Z INFO idle\n" +
      "2024-01-15T10:10:00Z ERR signal_lost\n2024-01-15T10:11:00Z INFO retry=3\n",
    "/etc/hosts": "127.0.0.1\tlocalhost\n::1\tlocalhost\n",
    "/etc/passwd": "root:x:0:0:root:/root:/bin/sh\nguest:x:1000:1000:guest:/home/guest:/bin/sh\n",
  };

  var DIRS = {
    "/": ["home", "etc", "var", ".", ".."],
    "/home": ["guest", ".", ".."],
    "/home/guest": ["readme.txt", "docs", "draft", RECOVERY_VNODE, NOSTALGIA_VNODE, ".", ".."],
    "/home/guest/docs": ["note.txt", ".", ".."],
    "/etc": ["hosts", "passwd", ".", ".."],
    "/var": ["log", ".", ".."],
    "/var/log": ["app.log", ".", ".."],
  };

  function draftFileRows() {
    var raw = document.body.getAttribute("data-cli-draft-index");
    if (!raw) return [];
    try {
      var arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function hiddenLinkRows() {
    var raw = document.body.getAttribute("data-cli-hidden-links");
    if (raw) {
      try {
        var arr = JSON.parse(raw);
        if (Array.isArray(arr)) return arr;
      } catch (e) {}
    }
    var h = document.body.getAttribute("data-cli-hidden-href");
    if (h)
      return [
        {
          href: h,
          label: "«Вы верите в Бога?»",
          catFile: "._____verite._node",
        },
      ];
    return [];
  }

  /** /home/guest/draft/<name>.md → черновик на сайте */
  function findDraftEntry(resolved) {
    if (resolved.indexOf("/home/guest/draft/") !== 0) return null;
    var base = "/home/guest/draft/";
    var name = resolved.slice(base.length);
    if (!name) return null;
    var rows = draftFileRows();
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].name === name) return rows[i];
    }
    return null;
  }

  /** Полный путь /home/guest/<catFile> → запись со ссылкой на статью */
  function findArticleEntry(resolved) {
    var rows = hiddenLinkRows();
    for (var i = 0; i < rows.length; i++) {
      if (!rows[i].catFile) continue;
      if (resolved === "/home/guest/" + rows[i].catFile) return rows[i];
    }
    return null;
  }

  /** Содержимое каталога (в ~ — vnode скрытых статей; в ~/draft — список черновиков) */
  function dirEntries(path) {
    if (path === "/home/guest/draft") {
      var drows = draftFileRows();
      var names = drows.map(function (r) {
        return r.name;
      });
      return names.concat([".", ".."]);
    }
    var base = DIRS[path];
    if (!base) return null;
    if (path !== "/home/guest") return base;
    var out = base.slice();
    var rows = hiddenLinkRows();
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].catFile) out.push(rows[i].catFile);
    }
    return out;
  }

  function hrefRecovery() {
    return document.body.getAttribute("data-cli-recovery-href") || "";
  }

  function decodeB64Utf8(b64) {
    if (!b64) return null;
    try {
      var bin = atob(b64);
      var u8 = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      return new TextDecoder("utf-8").decode(u8);
    } catch (e) {
      return null;
    }
  }

  function recoveryTextInline() {
    return decodeB64Utf8(document.body.getAttribute("data-cli-recovery-b64"));
  }

  function nostalgiaTextInline() {
    return decodeB64Utf8(document.body.getAttribute("data-cli-nostalgia-b64"));
  }

  function hrefNostalgia() {
    return document.body.getAttribute("data-cli-nostalgia-href") || "";
  }

  function isDir(p) {
    if (p === "/home/guest/draft") return true;
    return Object.prototype.hasOwnProperty.call(DIRS, p);
  }

  function resolvePath(cwd, raw) {
    if (!raw) return null;
    var base = raw[0] === "/" ? "" : cwd;
    var parts = (base + "/" + raw).split("/").filter(Boolean);
    var stack = [];
    for (var i = 0; i < parts.length; i++) {
      if (parts[i] === "..") {
        if (stack.length) stack.pop();
      } else if (parts[i] !== ".") stack.push(parts[i]);
    }
    return "/" + stack.join("/");
  }

  function promptPath(cwd) {
    if (cwd === "/home/guest") return "~";
    if (cwd === "/home/guest/draft") return "~/draft";
    return cwd;
  }

  function tokenize(line) {
    var out = [];
    var cur = "";
    var i = 0;
    while (i < line.length) {
      var c = line[i];
      if (c === " " || c === "\t") {
        if (cur) {
          out.push(cur);
          cur = "";
        }
        i++;
        continue;
      }
      cur += c;
      i++;
    }
    if (cur) out.push(cur);
    return out;
  }

  function parseLsFlags(args) {
    var flags = { a: false, l: false, h: false };
    for (var i = 0; i < args.length; i++) {
      var a = args[i];
      if (a[0] !== "-") break;
      if (a === "--") break;
      for (var j = 1; j < a.length; j++) {
        var ch = a[j];
        if (ch === "a") flags.a = true;
        else if (ch === "l") flags.l = true;
        else if (ch === "h") flags.h = true;
      }
    }
    return flags;
  }

  function lsTargetPath(args, cwd) {
    var pathArg = null;
    for (var i = 0; i < args.length; i++) {
      if (args[i][0] === "-") continue;
      pathArg = args[i];
      break;
    }
    if (!pathArg) return cwd;
    var r = resolvePath(cwd, pathArg);
    return r || cwd;
  }

  function fileSize(path) {
    if (path === "/home/guest/" + RECOVERY_VNODE) return 4096;
    if (path === "/home/guest/" + NOSTALGIA_VNODE) return 3072;
    if (findDraftEntry(path)) return 2048;
    if (findArticleEntry(path)) return 512;
    var c = FILES[path];
    if (c) return c.length;
    return 0;
  }

  function longListing(name, fullPath, flags) {
    var sz = fileSize(fullPath);
    var szStr = flags.h && sz >= 1024 ? Math.round(sz / 1024) + "K" : String(sz);
    var secret =
      name === RECOVERY_VNODE ||
      name === NOSTALGIA_VNODE ||
      !!findArticleEntry(fullPath);
    var mark = secret ? "-" : "-rw-r--r--";
    var owner = secret ? "root" : "guest";
    return mark + "  1 " + owner + "  staff  " + szStr + "  Jan 15 10:00  " + name;
  }

  function runLs(cwd, args, println) {
    var flags = parseLsFlags(args.slice(1));
    var dir = lsTargetPath(args.slice(1), cwd);
    if (!isDir(dir)) {
      println("ls: cannot access '" + (args[args.length - 1] || ".") + "': No such file or directory");
      return;
    }
    var entries = dirEntries(dir);
    if (!entries) return;
    var names = entries.filter(function (n) {
      if (n === "." || n === "..") return flags.a;
      if (n[0] === ".") return flags.a;
      return true;
    });
    names = names.slice().sort(function (a, b) {
      return a.localeCompare(b);
    });
    if (!flags.l) {
      println(names.join("  "));
      return;
    }
    for (var i = 0; i < names.length; i++) {
      var n = names[i];
      var fp = dir === "/" ? "/" + n : dir + "/" + n;
      if (n === "." || n === "..") println("drwxr-xr-x  2 guest  staff  64  Jan 15 10:00  " + n);
      else if (isDir(fp)) println("drwxr-xr-x  2 guest  staff  64  Jan 15 10:00  " + n);
      else println(longListing(n, fp, flags));
    }
  }

  function runTree(cwd, args, println) {
    var maxD = 2147483647;
    var start = cwd;
    var i = 1;
    if (args[i] === "-L" && args[i + 1]) {
      maxD = parseInt(args[i + 1], 10) || 1;
      i += 2;
    }
    if (args[i]) start = resolvePath(cwd, args[i]) || cwd;
    if (!isDir(start)) {
      println("tree: invalid directory");
      return;
    }
    println(start);
    function walk(path, prefix, depth) {
      if (depth > maxD) return;
      var ent = dirEntries(path);
      if (!ent) return;
      var names = ent.filter(function (n) {
        return n !== "." && n !== "..";
      });
      names.sort();
      for (var j = 0; j < names.length; j++) {
        var name = names[j];
        var full = path === "/" ? "/" + name : path + "/" + name;
        var last = j === names.length - 1;
        var branch = last ? "└── " : "├── ";
        println(prefix + branch + name);
        if (isDir(full) && depth < maxD) {
          walk(full, prefix + (last ? "    " : "│   "), depth + 1);
        }
      }
    }
    walk(start, "", 1);
  }

  function virtualFileKind(resolved) {
    if (resolved === "/home/guest/" + RECOVERY_VNODE) return "recovery";
    if (resolved === "/home/guest/" + NOSTALGIA_VNODE) return "nostalgia";
    return null;
  }

  function readFile(resolved, cb) {
    var vkind = virtualFileKind(resolved);
    if (vkind === "recovery") {
      var rtxt = recoveryTextInline();
      if (rtxt != null && rtxt !== "") {
        cb(null, rtxt);
        return;
      }
      var rurl = hrefRecovery();
      if (!rurl) {
        cb("cat: " + RECOVERY_VNODE + ": нет data-cli-recovery-b64 и recovery href");
        return;
      }
      fetch(rurl)
        .then(function (r) {
          if (!r.ok) throw new Error(r.statusText);
          return r.text();
        })
        .then(function (t) {
          cb(null, t);
        })
        .catch(function (e) {
          cb("cat: " + RECOVERY_VNODE + ": " + (e.message || "fetch failed"));
        });
      return;
    }
    if (vkind === "nostalgia") {
      var ntxt = nostalgiaTextInline();
      if (ntxt != null && ntxt !== "") {
        cb(null, ntxt);
        return;
      }
      var nurl = hrefNostalgia();
      if (!nurl) {
        cb("cat: " + NOSTALGIA_VNODE + ": нет data-cli-nostalgia-b64 и href");
        return;
      }
      fetch(nurl)
        .then(function (r) {
          if (!r.ok) throw new Error(r.statusText);
          return r.text();
        })
        .then(function (t) {
          cb(null, t);
        })
        .catch(function (e) {
          cb("cat: " + NOSTALGIA_VNODE + ": " + (e.message || "fetch failed"));
        });
      return;
    }
    if (FILES[resolved]) {
      cb(null, FILES[resolved]);
      return;
    }
    if (isDir(resolved)) {
      cb("cat: " + resolved + ": Is a directory");
      return;
    }
    cb("cat: No such file or directory");
  }

  function runCd(cwd, prevCwd, args) {
    var target = args[1];
    if (!target || target === "~") {
      return { cwd: "/home/guest", prev: cwd };
    }
    if (target === "-") {
      if (!prevCwd) {
        return { err: "cd: OLDPWD not set", cwd: cwd, prev: prevCwd };
      }
      return { cwd: prevCwd, prev: cwd, pwdOut: prevCwd };
    }
    var r = resolvePath(cwd, target);
    if (!r || !isDir(r)) {
      return { err: "cd: no such file or directory: " + target, cwd: cwd, prev: prevCwd };
    }
    return { cwd: r, prev: cwd };
  }

  function parseHeadTail(args, which) {
    var n = 10;
    var follow = false;
    var i = 1;
    while (i < args.length && args[i][0] === "-") {
      var a = args[i];
      if (which === "tail" && a === "-f") {
        follow = true;
        i++;
        continue;
      }
      if (a === "-n" && args[i + 1]) {
        n = parseInt(args[i + 1], 10) || n;
        i += 2;
        continue;
      }
      if (a.length > 2 && a.slice(0, 2) === "-n") {
        n = parseInt(a.slice(2), 10) || n;
        i++;
        continue;
      }
      break;
    }
    return { n: n, file: args[i], follow: follow };
  }

  var HELP_TEXT = [
    "Доступные команды (учебная симуляция):",
    "",
    "  pwd",
    "      Print Working Directory — текущая папка (пример: pwd).",
    "",
    "  ls [-lah] [путь]",
    "      List — список файлов и папок. Пример: ls -la",
    "      -l  детальный вид (права, владелец, размер)",
    "      -a  скрытые файлы (с точки)",
    "      -h  human-readable (размер в K/M, где применимо)",
    "",
    "  cd [путь]",
    "      Change Directory. Примеры: cd /etc   cd ..   cd ~   cd -",
    "",
    "  tree [-L N] [путь]",
    "      структура папок деревом (пример: tree -L 2). Отдельный пакет не нужен.",
    "",
    "  cat файл",
    "      весь вывод файла в терминал (пример: cat file.txt).",
    "",
    "  less файл",
    "      листать большой файл; в настоящем less: q — выход, / — поиск.",
    "      Здесь выводится файл целиком.",
    "",
    "  head [-n N] файл",
    "      первые N строк (по умолчанию 10). Пример: head -n 20 file.txt",
    "",
    "  tail [-n N] [-f] файл",
    "      последние N строк; -f (follow) — хвост лога в реальном времени.",
    "      В симуляции -f только поясняется, поток не обновляется.",
    "",
    "  help",
    "      этот список.",
    "",
  ].join("\n");

  function openShell() {
    if (shown || !document.body) return;
    shown = true;
    try {
      sessionStorage.setItem(SK, "0");
    } catch (e) {}

    var cwd = "/home/guest";
    var prevCwd = null;

    var ov = document.createElement("div");
    ov.id = "talos-cli-overlay";
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-label", "Командная строка");
    ov.innerHTML =
      '<div class="talos-cli-panel">' +
      '<div class="talos-cli-head">guest@loc — session</div>' +
      '<div class="talos-cli-out" id="talos-cli-out"></div>' +
      '<div class="talos-cli-line">' +
      '<span class="talos-cli-prompt" id="talos-cli-prompt">guest@loc:~$ </span>' +
      '<input type="text" class="talos-cli-input" id="talos-cli-input" autocomplete="off" spellcheck="false" autocapitalize="off" />' +
      "</div>" +
      '<p class="talos-cli-hint">Esc — выход</p>' +
      "</div>";
    document.body.appendChild(ov);
    var out = document.getElementById("talos-cli-out");
    var inp = document.getElementById("talos-cli-input");
    var promptEl = document.getElementById("talos-cli-prompt");

    function syncPrompt() {
      if (promptEl) promptEl.textContent = "guest@loc:" + promptPath(cwd) + "$ ";
    }

    function println(t) {
      var line = document.createElement("div");
      line.className = "talos-cli-line-out";
      line.textContent = t;
      out.appendChild(line);
      out.scrollTop = out.scrollHeight;
    }

    function printBlock(t) {
      var line = document.createElement("div");
      line.className = "talos-cli-line-out talos-cli-line-out--pre";
      line.textContent = t;
      out.appendChild(line);
      out.scrollTop = out.scrollHeight;
    }

    syncPrompt();
    inp.focus();

    function runLine(raw) {
      var line = raw;
      println("guest@loc:" + promptPath(cwd) + "$ " + line);
      var t = line.trim();
      if (!t) return;

      var args = tokenize(t);
      var cmd0 = args[0].toLowerCase();

      if (cmd0 === "help" || cmd0 === "?") {
        printBlock(HELP_TEXT);
        return;
      }

      if (cmd0 === "pwd") {
        println(cwd);
        return;
      }

      if (cmd0 === "cd") {
        var cr = runCd(cwd, prevCwd, args);
        if (cr.err) {
          println(cr.err);
          return;
        }
        prevCwd = cr.prev;
        cwd = cr.cwd;
        if (cr.pwdOut) println(cr.pwdOut);
        syncPrompt();
        return;
      }

      if (cmd0 === "ls") {
        runLs(cwd, args, println);
        return;
      }

      if (cmd0 === "tree") {
        runTree(cwd, args, println);
        return;
      }

      if (cmd0 === "cat") {
        if (!args[1]) {
          println("cat: missing file operand");
          return;
        }
        var pathCat = resolvePath(cwd, args[1]);
        if (!pathCat) {
          println("cat: invalid path");
          return;
        }
        var dr = findDraftEntry(pathCat);
        if (dr && dr.href) {
          println("→ открываю " + (dr.title || dr.name));
          window.location.assign(dr.href);
          return;
        }
        var art = findArticleEntry(pathCat);
        if (art && art.href) {
          println("→ открываю " + (art.label || art.href));
          window.location.assign(art.href);
          return;
        }
        readFile(pathCat, function (err, text) {
          if (err) println(err);
          else printBlock(text);
        });
        return;
      }

      if (cmd0 === "less") {
        if (!args[1]) {
          println("less: missing file operand");
          return;
        }
        var pathLess = resolvePath(cwd, args[1]);
        if (!pathLess) {
          println("less: invalid path");
          return;
        }
        readFile(pathLess, function (err, text) {
          if (err) {
            println(err);
            return;
          }
          println("(less — в полной версии: q выход, / поиск, стрелки прокрутка; здесь вывод целиком)");
          printBlock(text);
          println("(END)");
        });
        return;
      }

      if (cmd0 === "head") {
        var ph = parseHeadTail(args, "head");
        if (!ph.file) {
          println("head: missing file operand");
          return;
        }
        var pathH = resolvePath(cwd, ph.file);
        if (!pathH) {
          println("head: invalid path");
          return;
        }
        readFile(pathH, function (err, text) {
          if (err) {
            println(err);
            return;
          }
          var lines = text.split("\n");
          var slice = lines.slice(0, ph.n).join("\n");
          printBlock(slice);
        });
        return;
      }

      if (cmd0 === "tail") {
        var pt = parseHeadTail(args, "tail");
        if (!pt.file) {
          println("tail: missing file operand");
          return;
        }
        var pathT = resolvePath(cwd, pt.file);
        if (!pathT) {
          println("tail: invalid path");
          return;
        }
        readFile(pathT, function (err, text) {
          if (err) {
            println(err);
            return;
          }
          var lines = text.split("\n");
          if (lines.length && lines[lines.length - 1] === "") lines.pop();
          var slice = lines.slice(-pt.n).join("\n");
          printBlock(slice);
          if (pt.follow) println("[follow: в симуляции поток не обновляется — в настоящем tail -f ждёт новые строки]");
        });
        return;
      }

      println("command not found: " + args[0]);
    }

    inp.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        ov.remove();
        shown = false;
        return;
      }
      if (e.key !== "Enter") return;
      e.preventDefault();
      var line = inp.value;
      inp.value = "";
      runLine(line);
    });
  }

  function onThemeClick() {
    try {
      var n = parseInt(sessionStorage.getItem(SK) || "0", 10) + 1;
      sessionStorage.setItem(SK, String(n));
      if (n >= CLICKS) openShell();
    } catch (e) {}
  }

  function init() {
    var btn = document.getElementById("theme-toggle");
    if (btn) btn.addEventListener("click", onThemeClick);
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", init);
  else init();
})();
