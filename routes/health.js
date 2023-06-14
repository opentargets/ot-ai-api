import express from "express";
import * as dotenv from "dotenv";

dotenv.config();
const router = express.Router();

router.get("/", async (req, res) => {
  res.json({
    health: "ok",
  });
});

export default router;
