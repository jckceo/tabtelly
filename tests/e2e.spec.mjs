/* global window, document, AudioContext */
import { test, expect } from '@playwright/test';

async function pairReceiver(sender, receiver) {
  const code = await sender.evaluate(() => window.TABCAST.pairCode);
  await receiver.goto('/tv');
  await receiver.locator('input').fill(code);
  await receiver.getByRole('button', { name: /pair|connect/i }).click();
  await expect(sender.locator('#tvState')).toContainText(/connected|ready/i);
}

async function installSyntheticCapture(page) {
  // Exercise actual Chromium RTCPeerConnection with generated moving video and
  // audio. The operating-system picker and physical devices remain manual tests.
  await page.addInitScript(() => {
    Object.defineProperty(window, 'documentPictureInPicture', { value: undefined });
    window.__captures = 0;
    navigator.mediaDevices.getDisplayMedia = async () => {
      window.__captures++;
      const canvas = document.createElement('canvas');
      canvas.width = 640; canvas.height = 360;
      const ctx = canvas.getContext('2d');
      let n = 0;
      const draw = () => {
        ctx.fillStyle = n++ % 2 ? '#237a53' : '#154930';
        ctx.fillRect(0, 0, 640, 360);
        ctx.fillStyle = 'white'; ctx.font = '40px sans-serif';
        ctx.fillText(`TabTelly test ${n}`, 30, 100);
      };
      draw();
      const timer = setInterval(draw, 33);
      const stream = canvas.captureStream(30);
      const audio = new AudioContext();
      await audio.resume();
      const tone = audio.createOscillator();
      const gain = audio.createGain(); gain.gain.value = 0.03;
      const destination = audio.createMediaStreamDestination();
      tone.connect(gain).connect(destination); tone.start();
      stream.addTrack(destination.stream.getAudioTracks()[0]);
      const track = stream.getVideoTracks()[0];
      const realStop = track.stop.bind(track);
      track.stop = () => { clearInterval(timer); tone.stop(); audio.close(); realStop(); };
      return stream;
    };
  });
}

async function assertMedia(receiver) {
  await expect.poll(() => receiver.locator('#v').evaluate(v => v.videoWidth)).toBe(640);
  await expect.poll(() => receiver.evaluate(async () => {
    return document.getElementById('v').currentTime;
  })).toBeGreaterThan(0.1);
}

test('pairing rejects a wrong code and supports keyboard submission', async ({ page, context }) => {
  await page.goto('/send');
  await expect(page.getByRole('heading', { name: 'TabTelly', exact: true })).toBeVisible();
  const receiver = await context.newPage();
  await receiver.goto('/tv');
  const correct = await page.evaluate(() => window.TABCAST.pairCode);
  const wrong = correct === '000000' ? '999999' : '000000';
  await receiver.locator('input').fill(wrong);
  await receiver.locator('input').press('Enter');
  await expect(receiver.locator('body')).toContainText(/incorrect|wrong|did not match|not valid/i);
  await receiver.locator('input').fill(correct);
  await receiver.locator('input').press('Enter');
  await expect(page.locator('#tvState')).toContainText(/connected|ready/i);
  await receiver.close();
});

test('encrypted WebRTC receives moving video and audio, switches, reloads, rejects a second sender, and stops', async ({ page, context }) => {
  const errors = [];
  page.on('pageerror', err => errors.push(err.message));
  await installSyntheticCapture(page);
  await page.goto('/send');
  const receiver = await context.newPage();
  receiver.on('pageerror', err => errors.push(err.message));
  await pairReceiver(page, receiver);
  await page.locator('#start').click();
  await assertMedia(receiver);
  // Inspect the real inbound audio track; the audible output itself needs a TV.
  await expect.poll(() => receiver.locator('#v').evaluate(v => v.srcObject && v.srcObject.getAudioTracks().length)).toBe(1);
  await expect.poll(async () => {
    const status = await page.evaluate(async () => (await fetch('/status', { headers: { 'X-Tabcast-Token': window.TABCAST.senderToken } })).json());
    return status.tv.report.audio?.kbps || 0;
  }).toBeGreaterThan(0);
  await page.locator('#switch').click();
  await expect.poll(() => page.evaluate(() => window.__captures)).toBe(2);
  await assertMedia(receiver);
  await receiver.reload();
  await assertMedia(receiver);
  const second = await context.newPage();
  await installSyntheticCapture(second);
  await second.goto('/send');
  await expect(second.locator('#tvState')).toContainText(/another|busy/i);
  await expect(second.locator('#start')).toBeDisabled();
  await second.close();
  await page.locator('#stop').click();
  await expect(receiver.locator('#idle')).toBeVisible();
  await expect(receiver.locator('#v')).toHaveJSProperty('srcObject', null);
  expect(errors).toEqual([]);
  await receiver.close();
});

test('sender fits a narrow viewport and pairing controls fit a 720p TV', async ({ page, context }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/send');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await expect(page.locator('#quality')).toBeVisible();
  const receiver = await context.newPage();
  await receiver.setViewportSize({ width: 1280, height: 720 });
  await receiver.goto('/tv');
  const box = await receiver.locator('#pairButton').boundingBox();
  expect(box.y).toBeGreaterThanOrEqual(0);
  expect(box.y + box.height).toBeLessThanOrEqual(720);
  expect(await receiver.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await receiver.close();
});

test('a receiver without WebRTC keeps an actionable compatibility error', async ({ page, context }) => {
  await page.goto('/send');
  const code = await page.evaluate(() => window.TABCAST.pairCode);
  const receiver = await context.newPage();
  await receiver.addInitScript(() => Object.defineProperty(window, 'RTCPeerConnection', { value: undefined }));
  await receiver.goto('/tv');
  await receiver.locator('input').fill(code);
  await receiver.getByRole('button', { name: 'Pair TV' }).click();
  await expect(receiver.locator('#tvState')).toContainText(/does not support WebRTC/i);
  await expect(page.locator('#start')).toBeDisabled();
  await expect(page.locator('#tvState')).toContainText(/unsupported|WebRTC|not support/i);
  await receiver.close();
});
