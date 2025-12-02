import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(request: NextRequest) {
  try {
    const { email, type } = await request.json();

    if (!email) {
      return NextResponse.json({ error: "Email is required" }, { status: 400 });
    }

    // Send notification email
    await resend.emails.send({
      from: "Brutally Honest <noreply@brutallyhonest.io>",
      to: ["daniel@altfawesome.nl"],
      subject: type === "waitlist" 
        ? `New Waitlist Signup: ${email}` 
        : `New Contact Request: ${email}`,
      html: `
        <h2>New ${type === "waitlist" ? "Waitlist Signup" : "Contact Request"}</h2>
        <p><strong>Email:</strong> ${email}</p>
        <p><strong>Time:</strong> ${new Date().toISOString()}</p>
        <p><strong>Type:</strong> ${type}</p>
      `,
    });

    // Send confirmation to user
    await resend.emails.send({
      from: "Brutally Honest <noreply@brutallyhonest.io>",
      to: [email],
      subject: "Welcome to Brutally Honest - You're on the list! 🎉",
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fff; padding: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            .logo { margin-bottom: 32px; }
            h1 { font-size: 28px; margin-bottom: 16px; }
            p { color: #a0a0a0; line-height: 1.6; }
            .highlight { color: #fff; }
            .button { display: inline-block; background: #fff; color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin-top: 24px; font-weight: 500; }
            .footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid #2a2a2a; font-size: 12px; color: #666; }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>You're on the early access list! 🎉</h1>
            <p>Thanks for signing up for <span class="highlight">Brutally Honest</span>.</p>
            <p>We're building the future of real-time fact-checking for interviews, meetings, and negotiations. You'll be among the first to know when we launch.</p>
            <p>In the meantime, if you'd like to try our early access version, click the button below:</p>
            <a href="https://app.brutallyhonest.io" class="button">Try Early Access →</a>
            <div class="footer">
              <p>© ${new Date().getFullYear()} ALT F AWESOME — All rights reserved.</p>
              <p>Questions? Reply to this email or reach us at daniel@altfawesome.nl</p>
            </div>
          </div>
        </body>
        </html>
      `,
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Contact form error:", error);
    return NextResponse.json(
      { error: "Failed to send email" },
      { status: 500 }
    );
  }
}

