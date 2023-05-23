const axios = require("axios");
const { XMLParser } = require("fast-xml-parser");

function europePmcSearchPOSTQuery(id) {
  const baseUrl = `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC${id}/fullTextXML`;
  return { baseUrl };
}

function getPlainText({ pubBodyJson }) {
  let str = "";

  const hanblePChild = (par, title) => {
    const isParArr = Array.isArray(par);
    let sectionText = title + "\n ";
    if (isParArr) {
      par.forEach((p) => {
        let text = "";
        if (typeof p === "string") {
          text = p + "\n";
        } else {
          text = p["#text"] + "\n";
        }
        sectionText += text;
      });
    } else {
      let text = "";
      if (typeof par === "object") {
        text = par["#text"] + "\n";
      }
      if (typeof par === "string") {
        text = par + "\n";
      }
      sectionText += text;
    }
    return sectionText;
  };

  const handleSecChild = (element) => {
    element.sec.forEach((section) => {
      const title = section.title;
      const par = section.p;
      const childSec = section.sec;
      if (!par && !childSec) return;
      if (par) {
        str += hanblePChild(par, title);
      }
      if (childSec) {
        handleSecChild(section);
      }
    });
  };

  handleSecChild(pubBodyJson);

  return str;
}

async function handleLiterartureRequest({ id }) {
  const { baseUrl } = europePmcSearchPOSTQuery(id);
  const requestOptions = {
    method: "GET",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    },
  };

  let json = null;
  let str = "";
  const parser = new XMLParser();
  await axios.get(baseUrl, requestOptions).then(({ data: XMLData }) => {
    const jsonData = parser.parse(XMLData);
    const pubBodyJson = jsonData.article.body;

    const response = getPlainText({ pubBodyJson });

    str = response;
    json = pubBodyJson;
  });
  return str;
}

module.exports = { handleLiterartureRequest };
