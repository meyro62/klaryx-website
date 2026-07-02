// ============================================================
// KLARYX APPS SCRIPT - Vollständige Version 2
// KOMPLETTEN bestehenden Code ersetzen mit diesem
// ============================================================

function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var wallet = e.parameter.wallet;
  var einladungscode = e.parameter.einladungscode || "–";
  
  // Neue Registrierung
  if (wallet && !e.parameter.archivieren) {
    var sheet = ss.getSheetByName("Ausstehend");
    var now = new Date();
    var datum = Utilities.formatDate(now, "Europe/Berlin", "dd.MM.yyyy");
    var uhrzeit = Utilities.formatDate(now, "Europe/Berlin", "HH:mm:ss");
    sheet.appendRow([datum, uhrzeit, wallet, einladungscode, "Ausstehend", ""]);
  }
  
  // Archivieren nach Versand
  if (e.parameter.archivieren === "1") {
    var gesendetAm = e.parameter.gesendet || "";
    var ausstehend = ss.getSheetByName("Ausstehend");
    var archiv = ss.getSheetByName("Archiv");
    var data = ausstehend.getDataRange().getValues();
    
    for (var i = data.length - 1; i >= 1; i--) {
      if (data[i][2] === wallet) {
        var row = data[i];
        row[4] = "Gesendet";
        row[5] = gesendetAm;
        archiv.appendRow(row);
        ausstehend.deleteRow(i + 1);
        break;
      }
    }
  }
  
  return ContentService.createTextOutput("OK").setMimeType(ContentService.MimeType.TEXT);
}

function doPost(e) {
  var data = JSON.parse(e.postData.contents);
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Ausstehend");
  var now = new Date();
  var datum = Utilities.formatDate(now, "Europe/Berlin", "dd.MM.yyyy");
  var uhrzeit = Utilities.formatDate(now, "Europe/Berlin", "HH:mm:ss");
  sheet.appendRow([datum, uhrzeit, data.wallet, data.einladungscode || "–", "Ausstehend", ""]);
  return ContentService.createTextOutput("OK").setMimeType(ContentService.MimeType.TEXT);
}

// ============================================================
// BADGE SYSTEM
// ============================================================
function badgesAktualisieren() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var ausstehend = ss.getSheetByName("Ausstehend");
  var archiv = ss.getSheetByName("Archiv");
  var badges = ss.getSheetByName("Badges");
  
  if (!badges) {
    badges = ss.insertSheet("Badges");
    badges.appendRow(["Wallet", "Anzahl Einladungen", "Badge", "Bonus KLRX", "Bonus Status"]);
  }
  
  var referrerCounts = {};
  
  function countReferrals(sheet) {
    if (!sheet) return;
    var data = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      var referrer = data[i][3];
      if (referrer && referrer !== "–" && referrer.length > 20) {
        referrerCounts[referrer] = (referrerCounts[referrer] || 0) + 1;
      }
    }
  }
  
  countReferrals(ausstehend);
  countReferrals(archiv);
  
  var bestehendeBoni = {};
  var badgeData = badges.getDataRange().getValues();
  for (var i = 1; i < badgeData.length; i++) {
    bestehendeBoni[badgeData[i][0]] = badgeData[i][4];
  }
  
  badges.clear();
  badges.appendRow(["Wallet", "Anzahl Einladungen", "Badge", "Stufen-Bonus KLRX", "Bonus Status", "Tier-Zugang"]);
  
  for (var wallet in referrerCounts) {
    var count = referrerCounts[wallet];
    var badge = "";
    var bonus = 0;
    var tier = "Free";

    if (count >= 100) { badge = "👑 Legend"; bonus = 2.00; tier = "Tiefe + Hall of Fame"; }
    else if (count >= 50) { badge = "💠 Diamant"; bonus = 1.00; tier = "Tiefe"; }
    else if (count >= 25) { badge = "💎 Platin"; bonus = 0.50; tier = "Einblick"; }
    else if (count >= 10) { badge = "🥇 Gold"; bonus = 0.15; tier = "Free"; }
    else if (count >= 5) { badge = "🥈 Silber"; bonus = 0.05; tier = "Free"; }
    else if (count >= 1) { badge = "🥉 Bronze"; bonus = 0; tier = "Free"; }
    
    // Referral-Boni: 0.005 KLRX pro Einladung
    var referralBonus = count * 0.005;
    var gesamtBonus = bonus + referralBonus;
    
    var status = bestehendeBoni[wallet] || (gesamtBonus > 0 ? "Ausstehend" : "–");
    
    badges.appendRow([wallet, count, badge, gesamtBonus.toFixed(3), status, tier]);
  }
}

function dailyBadgeUpdate() {
  badgesAktualisieren();
}
