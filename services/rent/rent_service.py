import requests
from datetime import datetime

RENT_API = "http://localhost:5000/api"

async def handle_rent(message, text):
    parts  = text.strip().split()
    action = parts[1].lower() if len(parts) > 1 else None

    # ── !rent (no action) — show help ────────────────────────
    if action is None:
        await message.reply("""```
🏠 Rent Commands:
!rent list                                         → all active tenants
!rent dues                                         → who still owes money
!rent summary                                      → this month's overview
!rent tenant <id>                                  → view single tenant
!rent add <name> <room> <phone> <rent>             → add new tenant
!rent bill <tenantId> <units> <rate> <fee> <note>  → generate bill
!rent pay <tenantId> <billId> <amount> <method>    → record payment
!rent history <tenantId>                           → payment history
!rent archive <tenantId>                           → mark as moved out
``````""")
        return

    # ── !rent list ───────────────────────────────────────────
    if action == "list":
        try:
            r = requests.get(f"{RENT_API}/tenants")
            tenants = r.json()
            if not tenants:
                await message.reply("📭 No active tenants found.")
                return
            msg = "```\n🏠 Active Tenants:\n"
            msg += f"{'ID':<5} {'Name':<25} {'Room':<8} {'Monthly Rent':>12}\n"
            msg += "─" * 54 + "\n"
            for t in tenants:
                msg += f"{t['id']:<5} {t['fullName']:<25} {t['roomNumber']:<8} Rs.{t['monthlyRent']:>10,.0f}\n"
            msg += "```"
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent tenant <id> ────────────────────────────────────
    elif action == "tenant":
        try:
            if len(parts) < 3:
                await message.reply("❌ Usage: `!rent tenant <id>`")
                return
            r = requests.get(f"{RENT_API}/tenants/{parts[2]}")
            if r.status_code == 404:
                await message.reply("❌ Tenant not found.")
                return
            t = r.json()
            msg = f"""```
👤 Tenant Details:
─────────────────────────────
ID            : {t['id']}
Name          : {t['fullName']}
Phone         : {t['phone']}
Emergency     : {t['emergencyContact']}
National ID   : {t['nationalId']}
Room          : {t['roomNumber']}
Move-in Date  : {t['moveInDate'][:10]}
Monthly Rent  : Rs.{t['monthlyRent']:,.0f}
Status        : {'✅ Active' if t['isActive'] else '🔴 Archived'}
`````"""
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent dues ───────────────────────────────────────────
    elif action == "dues":
        try:
            r = requests.get(f"{RENT_API}/bills/dues")
            dues = r.json()
            if not dues:
                await message.reply("✅ Everyone has paid! No pending dues.")
                return
            msg = "```\n⚠️  Pending Dues:\n"
            msg += f"{'TID':<5} {'Name':<22} {'Month':<8} {'Total Due':>10} {'Paid':>10} {'Remaining':>10}\n"
            msg += "─" * 69 + "\n"
            for b in dues:
                name = b.get('tenant', {}).get('fullName', 'Unknown')
                msg += (
                    f"{b['tenantId']:<5} {name:<22} "
                    f"{b['month']}/{b['year']:<4} "
                    f"Rs.{b['totalDue']:>8,.0f} "
                    f"Rs.{b['totalPaid']:>8,.0f} "
                    f"Rs.{b['remainingDue']:>8,.0f}\n"
                )
            msg += "```"
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent summary ────────────────────────────────────────
    elif action == "summary":
        try:
            now = datetime.now()
            r = requests.get(f"{RENT_API}/bills/summary/{now.month}/{now.year}")
            if r.status_code == 404:
                await message.reply("❌ No bills found for this month.")
                return
            s = r.json()
            msg = f"""```
📊 Monthly Summary — {s['month']}/{s['year']}
─────────────────────────────────────────────
Total Tenants  : {s['totalTenants']}
Total Due      : Rs.{s['totalDue']:,.0f}
Total Collected: Rs.{s['totalCollected']:,.0f}
Total Remaining: Rs.{s['totalRemaining']:,.0f}
─────────────────────────────────────────────
{'Name':<22} {'Due':>10} {'Paid':>10} {'Left':>10}
{'─'*54}
````"""
            for b in s.get('bills', []):
                msg += f"`{b['tenantName']:<22} Rs.{b['totalDue']:>8,.0f} Rs.{b['totalPaid']:>8,.0f} Rs.{b['remainingDue']:>8,.0f}`\n"
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent add <name> <room> <phone> <rent> ───────────────
    elif action == "add":
        try:
            if len(parts) < 6:
                await message.reply(
                    "❌ Usage: `!rent add <name> <room> <phone> <monthlyRent>`\n"
                    "Example: `!rent add Ram_Bahadur 101 9841000001 8000`\n"
                    "💡 Use underscore for spaces in name: `Ram_Bahadur`"
                )
                return
            name        = parts[2].replace("_", " ")
            room        = parts[3]
            phone       = parts[4]
            rent_amount = float(parts[5])
            payload = {
                "fullName"        : name,
                "roomNumber"      : room,
                "phone"           : phone,
                "emergencyContact": "N/A",
                "nationalId"      : "N/A",
                "moveInDate"      : "2026-01-01T00:00:00Z",
                "monthlyRent"     : rent_amount
            }
            r = requests.post(f"{RENT_API}/tenants", json=payload)
            t = r.json()
            await message.reply(
                f"✅ Tenant added!\n"
                f"ID: `{t['id']}` — **{t['fullName']}**\n"
                f"Room: {t['roomNumber']} | Rs.{t['monthlyRent']:,.0f}/month"
            )
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent bill <tenantId> <units> <rate> <fee> <note> ────
    elif action == "bill":
        try:
            if len(parts) < 5:
                await message.reply(
                    "❌ Usage: `!rent bill <tenantId> <units> <rate> [extraFee] [note]`\n"
                    "Example: `!rent bill 1 45 13 500 Garbage`"
                )
                return
            now = datetime.now()
            payload = {
                "tenantId"        : int(parts[2]),
                "month"           : now.month,
                "year"            : now.year,
                "electricityUnits": float(parts[3]),
                "electricityRate" : float(parts[4]),
                "extraFees"       : float(parts[5]) if len(parts) > 5 else 0,
                "extraFeeNote"    : parts[6] if len(parts) > 6 else ""
            }
            r = requests.post(f"{RENT_API}/bills", json=payload)
            b = r.json()
            msg = f"""```
🧾 Bill Generated — {b['month']}/{b['year']}
─────────────────────────────────────────────
Tenant ID     : {b['tenantId']}
Rent          : Rs.{b['rentAmount']:,.0f}
Electricity   : {b['electricityUnits']} units × Rs.{b['electricityRate']} = Rs.{b['electricityAmount']:,.0f}
Extra Fees    : Rs.{b['extraFees']:,.0f} {('(' + b['extraFeeNote'] + ')') if b.get('extraFeeNote') else ''}
─────────────────────────────────────────────
Total Due     : Rs.{b['totalDue']:,.0f}
Total Paid    : Rs.{b['totalPaid']:,.0f}
Remaining     : Rs.{b['remainingDue']:,.0f}
```"""
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent pay <tenantId> <billId> <amount> <method> ──────
    elif action == "pay":
        try:
            if len(parts) < 5:
                await message.reply(
                    "❌ Usage: `!rent pay <tenantId> <billId> <amount> [method]`\n"
                    "Example: `!rent pay 1 1 5000 Cash`\n"
                    "Methods: Cash, eSewa, Bank"
                )
                return
            payload = {
                "tenantId"     : int(parts[2]),
                "monthlyBillId": int(parts[3]),
                "amountPaid"   : float(parts[4]),
                "paymentMethod": parts[5] if len(parts) > 5 else "Cash",
                "note"         : ""
            }
            r = requests.post(f"{RENT_API}/payments", json=payload)
            p = r.json()
            await message.reply(
                f"✅ Payment recorded!\n"
                f"Rs.{p['amountPaid']:,.0f} via **{p['paymentMethod']}**\n"
                f"Tenant ID: `{p['tenantId']}` | Bill ID: `{p['monthlyBillId']}`"
            )
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent history <tenantId> ─────────────────────────────
    elif action == "history":
        try:
            if len(parts) < 3:
                await message.reply("❌ Usage: `!rent history <tenantId>`")
                return
            r = requests.get(f"{RENT_API}/payments/{parts[2]}")
            payments = r.json()
            if not payments:
                await message.reply("📭 No payment history found.")
                return
            msg = "```\n💰 Payment History:\n"
            msg += f"{'ID':<5} {'Date':<12} {'Amount':>12} {'Method':<10} {'Note'}\n"
            msg += "─" * 55 + "\n"
            for p in payments:
                date = p['paymentDate'][:10]
                note = p.get('note') or ''
                msg += f"{p['id']:<5} {date:<12} Rs.{p['amountPaid']:>10,.0f} {p['paymentMethod']:<10} {note}\n"
            msg += "```"
            await message.reply(msg)
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    # ── !rent archive <tenantId> ─────────────────────────────
    elif action == "archive":
        try:
            if len(parts) < 3:
                await message.reply("❌ Usage: `!rent archive <tenantId>`")
                return
            r = requests.delete(f"{RENT_API}/tenants/{parts[2]}")
            if r.status_code == 404:
                await message.reply("❌ Tenant not found.")
                return
            await message.reply(
                f"🔴 Tenant `{parts[2]}` archived.\n"
                f"Their full history is preserved."
            )
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

    else:
        await message.reply(f"❌ Unknown action `{action}`. Type `!rent` to see all commands.")
