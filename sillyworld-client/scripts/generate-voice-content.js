/**
 * Script to generate voice content text files for the Idea Pitching POC
 * 
 * This script creates text files containing all the speech content
 * that would be spoken in the application.
 */

const fs = require('fs');
const path = require('path');

// Create directory if it doesn't exist
const contentDir = path.join(__dirname, '../public/voice-content');
if (!fs.existsSync(contentDir)) {
  fs.mkdirSync(contentDir, { recursive: true });
}

// Define all the voice content
const voiceContent = {
  // Alex intro and coaching questions
  'alex_intro': "Hi, I'm Alex, your AI co-founder. Let's prepare your pitch together. I'll need some information about your business idea.",
  'alex_question_1': "What is your business idea?",
  'alex_question_2': "What problem does it solve and who is the target audience?",
  'alex_question_3': "What value does it create and what's the potential upside?",
  'alex_question_4': "Tell me about your team's background and expertise.",
  'alex_question_5': "How do you plan to use the funding?",
  'alex_question_6': "Describe your team culture and working style.",
  
  // Alex follow-ups
  'alex_followup_1': "That's an interesting concept! Let's explore how we can position this for investors.",
  'alex_followup_2': "Great insight on the problem space. Investors will want to know the market size here.",
  'alex_followup_3': "Excellent value proposition! This will be a key part of our pitch.",
  'alex_followup_4': "Impressive team credentials! VCs invest in people first, so this will strengthen our case.",
  'alex_followup_5': "This allocation makes sense. Investors will appreciate your clear plan for their capital.",
  'alex_followup_6': "Culture is crucial for scaling. This shows you're thinking about building a sustainable organization.",
  
  // Pitch presentations (3 variations)
  'pitch_ai': "Hello investors, I'm Alex representing our startup leveraging artificial intelligence to help small businesses automate customer support. Our solution significantly reduces costs and improves efficiency. The market opportunity is $5B. Our exceptional team includes former Google engineers. With your investment of $1.5M, we'll accelerate product development and go-to-market. Our team culture fosters innovation and customer obsession. Thank you for your consideration.",
  'pitch_blockchain': "Hello investors, I'm Alex representing our startup using blockchain technology to connect local farmers directly with restaurants. Our solution creates substantial value for our customers. The market opportunity is $120B annually. Our exceptional team includes successful founders. With your investment of $1.5M, we'll expand our market reach and scale our operations. Our team culture values excellence and sustainable growth. Thank you for your consideration.",
  'pitch_wearable': "Hello investors, I'm Alex representing our startup with an innovative approach to help people with respiratory conditions. Our solution creates substantial value for our customers. The market opportunity is growing rapidly. Our exceptional team includes industry experts. With your investment of $1.5M, we'll accelerate product development and go-to-market. Our team culture fosters innovation and customer obsession. Thank you for your consideration.",
  
  // Judge questions
  'judge_1_question_1': "How do you plan to acquire your first 100 customers?",
  'judge_1_question_2': "What's your customer acquisition cost and lifetime value?",
  'judge_1_question_3': "What makes your solution different from existing alternatives?",
  'judge_2_question_1': "Can you elaborate on your go-to-market strategy?",
  'judge_2_question_2': "How scalable is your technical infrastructure?",
  'judge_2_question_3': "What are the biggest risks to your business model?",
  'judge_3_question_1': "Tell me more about your team's background and why you're the right people to solve this problem.",
  'judge_3_question_2': "What's your revenue model and pricing strategy?",
  'judge_3_question_3': "How do you plan to use the investment capital specifically?",
  
  // Alex answers to judge questions
  'alex_answer_customers': "Absolutely! We're taking a three-pronged approach to customer acquisition. First, we're leveraging strategic partnerships with established players in the space. Second, we're implementing highly targeted content marketing focused on the specific pain points we solve. And third, we're running limited-time pilot programs that allow customers to experience the value with minimal risk. Our early tests show that direct outreach to decision-makers is yielding a 28% meeting conversion rate. We're confident we can reach our first 100 customers within 6 months of launch.",
  'alex_answer_cac_ltv': "Great question about unit economics. Our current CAC is projected at $950 per customer, which we expect to decrease by about 30% as we optimize our funnel. On the LTV side, our revenue model projects an average customer lifetime of 24 months with an average monthly value of $350. This gives us an LTV of approximately $8,400, and an LTV:CAC ratio of 8.8:1, which is well above the industry benchmark of 3:1.",
  'alex_answer_differentiation': "Our solution stands out in three key ways. First, we've developed proprietary technology that delivers 40% better results than the leading competitors. Second, our approach is much more user-friendly, with implementation taking days instead of months. And third, we've built our solution specifically for our target market, while competitors offer generic solutions that require significant customization. Early customers have validated these advantages, with 95% reporting they would recommend us to peers.",
  'alex_answer_go_to_market': "Our go-to-market strategy has four pillars. We're starting with direct sales to enterprise customers in the financial and healthcare sectors, where we have strong connections. Simultaneously, we're building a self-service platform for SMBs. We've also established partnerships with three industry-specific consultancies who will resell our solution. Finally, we're creating thought leadership content to drive inbound interest. This multi-channel approach allows us to capture different segments of the market efficiently.",
  'alex_answer_scalability': "We've architected our system for scalability from day one. We're using a microservices architecture deployed on Kubernetes, which allows us to scale individual components as needed. Our database layer uses sharding to handle growing data volumes, and we've implemented caching throughout the stack. We've already stress-tested the system to handle 100x our projected year-one user load, and we have a clear roadmap for further optimizations as we grow.",
  'alex_answer_risks': "We've identified three primary risks. First, regulatory changes could impact how we handle data, which we're mitigating by building privacy-first architecture and staying ahead of compliance requirements. Second, larger competitors could enter our niche, so we're focused on moving quickly to establish strong network effects. Third, we face execution risk in scaling our team, which is why we've brought on advisors who've successfully scaled similar businesses and implemented structured onboarding processes.",
  'alex_answer_team': "Our founding team brings complementary skills that perfectly position us to solve this problem. Our CEO previously built and sold a company in an adjacent space, our CTO led engineering at a major tech company and has deep expertise in our core technologies, and our Head of Product spent five years at our target customers experiencing this problem firsthand. Beyond the founding team, we've assembled advisors who've scaled similar businesses to $100M+ in revenue, and our early hires all bring 8+ years of relevant experience.",
  'alex_answer_revenue': "We've implemented a tiered subscription model with three levels based on usage volume and feature access. Our starter tier begins at $299 per month, our professional tier at $999, and enterprise at $2,499. We've validated these price points with potential customers, finding strong willingness to pay given the ROI we deliver. Additionally, we offer implementation services and premium support as add-ons, which we expect to contribute about 15% of revenue while improving retention.",
  'alex_answer_funding': "We'll allocate the funding across four key areas. 40% will go to engineering to enhance our core product and build the next generation of features on our roadmap. 30% will fund our go-to-market efforts, including hiring sales representatives and launching our marketing campaigns. 20% will support operations, including customer success to ensure strong retention. The remaining 10% provides runway buffer to ensure we can navigate any unexpected challenges while maintaining momentum.",
  
  // Judge feedback
  'judge_1_feedback': "I'm genuinely impressed with your innovative use of AI technology to solve a real market need. Your cost reduction metrics are compelling and I can see the potential for rapid growth. What particularly stood out to me was your exceptional team background from top tech companies. However, I'd like to see more detail on your platform defensibility against larger competitors. Overall, I'm excited about your potential and would like to support your journey.",
  'judge_2_feedback': "Your presentation was clear and compelling. I appreciate the thorough market analysis and the thoughtful approach to solving a significant pain point. The team's expertise is evident, and your go-to-market strategy seems well-considered. My main concern is around the competitive landscape and how you'll maintain your advantage as you scale. That said, I see strong potential here and believe with the right execution, you could capture significant market share.",
  'judge_3_feedback': "Thank you for your pitch. I'm impressed by the clarity of your vision and the depth of your understanding of the customer problem. Your unit economics look promising, though I'd want to see more validation of the customer acquisition costs. The team's background is strong, which is crucial for execution. I have some concerns about the timeline to profitability, but overall, I see this as an attractive opportunity with substantial upside potential.",
  
  // System messages
  'system_accept': "Congratulations! You've successfully secured the investment. The investors are excited to partner with you on your journey to build and scale your business.",
  'system_negotiate': "You've decided to negotiate for better terms. After some back and forth, the investors agree to a 15% higher valuation with the same investment amount, giving you more equity retention.",
  'system_reject': "You've decided to reject the current offers and explore other funding options. This is a bold move that gives you more time to refine your pitch and potentially secure better terms in the future.",
  'system_intro': "Welcome to the Idea Pitching experience. You'll work with your AI co-founder Alex to prepare and deliver a compelling pitch to venture capital investors.",
  'system_conclusion': "Thank you for participating in the Idea Pitching experience. We hope you enjoyed working with Alex and learning about the pitching process."
};

// Write each content item to a separate file
Object.entries(voiceContent).forEach(([key, content]) => {
  const filePath = path.join(contentDir, `${key}.txt`);
  fs.writeFileSync(filePath, content);
  console.log(`Generated ${filePath}`);
});

console.log('All voice content files generated successfully!'); 